'''
 Copyright 2022 Yingte Xu
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

# Dependent Type System Support
# To extend 'terms', inherbit from Term, and overload the following methods:
#  __eq__, substitute, eval

from __future__ import annotations
from typing import List, Tuple, Dict


# No polymorphism on different universe

class DTS_RuntimeError(RuntimeError):
    def __init__(self, msg : str):
        super().__init__(msg)

class Para:
    '''
    paremeter for functions
    Readonly. No copy needed in assignment.    
    '''
    def __init__(self, para_id : str, type : Term):
        self._para_id : str = para_id
        self._para_type : Term = type
    
    @property
    def id(self) -> str:
        return self._para_id

    @property
    def type(self) -> Term:
        return self._para_type

    @property
    def is_type(self) -> bool:
        '''
        decide whether the term is also a type
        '''
        return isinstance(self.type, Sort)

    def __str__(self) -> str:
        return self.id
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Para):
            # since id is unique
            return self.id == other.id
        else:
            raise NotImplemented

    def set_parent_env(self, parent : ParaMicroEnv) -> None:
        self.type.set_parent_env(parent)

    def substitute(self, para : Para, val : Term | Para) -> Para | Term:
        if self == para:
            return val

        return Para(self._para_id, self._para_type.substitute(para, val))

class ParaMicroEnv:
    '''
    The micro (but still inductive) environment for parameters in functions
    Micro means at every level only one parameter is stored.
    Note: naming overload is NOT allowed, and the users should pay attention
    '''

    def __init__(self, para : Para | None = None):
        '''
        para : None means no parameter defined in this environment
        '''
        self._parent_env : ParaMicroEnv | None = None
        self._para : Para | None = para
    
    @property
    def para(self) -> Para | None:
        return self._para
    
    @property
    def parent(self) -> ParaMicroEnv | None:
        '''
        should not be modified
        '''
        return self._parent_env

    def set_parent(self, parent : ParaMicroEnv | None) -> None:
        if parent is None:
            return
        if isinstance(parent, ParaMicroEnv):
            if self.parent is not None:
                raise DTS_RuntimeError("The parent environment has already been set.")
            # set the parent environment
            self._parent_env = parent
        else:
            raise Exception("unexpected situation")

    def get_term(self, ask_id : str) -> Term:
        '''
        Get the type term with the ask_id.
        ask_id: should be a string
        '''
        if self._para is not None:
            if self._para.id == ask_id:
                return self._para.type
        if self._parent_env is not None:
            return self._parent_env.get_term(ask_id)
        else:
            raise DTS_RuntimeError("Variable of id '" + ask_id + "' does not exist.")
    
    def __str__(self) -> str:
        return str(self._para)

class Term:
    '''
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, type : Term | None, para_env : ParaMicroEnv | None):
        self._type : Term | None = type
        self._para_env : ParaMicroEnv | None = para_env
    
    @property
    def type(self) -> Term:
        if self._type is None:
            raise DTS_RuntimeError("Maximum universe number reached.")
        return self._type
    
    @property
    def para_env(self) -> ParaMicroEnv | None:
        return self._para_env

    def set_parent_env(self, parent : ParaMicroEnv) -> None:
        if self._para_env is not None:
            self._para_env.set_parent(parent)

    @property
    def is_type(self) -> bool:
        '''
        decide whether the term is also a type
        '''
        return isinstance(self.type, Sort)
            
    def substitute(self, para : Para,  val : Term | Para) -> Term:
        '''
        return the new term with the parameter substituted
        WARNING: no type check for val is applied
        '''        

        return self

    def eval(self) -> Term:
        return self

    def __eq__(self, other) -> bool:
        return NotImplemented

class Sort(Term):
    '''
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, type : Sort | None, u_num : int):
        super().__init__(type, None)
        self._u_num : int = u_num

    def __str__(self) -> str:
        return "Sort " + str(self._u_num)

    @property
    def u_num(self) -> int:
        return self._u_num
    
    def __eq__(self, other : Sort) -> bool:
        # sorts only equal to sorts
        if isinstance(other, Sort):
            return self.u_num == other.u_num
        else:
            return False

class Axiom(Term):
    '''
    The axiom does not have an value, i.e. it does not depend on any value
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, axiom_id : str, type : Term):
        super().__init__(type, None)
        self._axiom_id : str = axiom_id

    @property
    def id(self) -> str:
        return self._axiom_id

    def __str__(self) -> str:
        return self._axiom_id

    def __eq__(self, other : Axiom) -> bool:
        if isinstance(other, Axiom):
            return self.id == other.id
        else:
            return False

class Var(Term):
    '''
    variable with identifier and value.
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, var_id : str, type : Term, value : Term):
        '''
        the variable value 'value' must be of the type 'type'
        '''
        super().__init__(type, None)
        self._var_id : str = var_id
        self._value : Term = value
    
    @property
    def id(self) -> str:
        return self._var_id
    
    @property
    def val(self) -> Term:
        return self._value

    def __str__(self) -> str:
        return self.id
    
    def __eq__(self, other : Term) -> bool:
        if isinstance(other, Var):
            if self.id == other.id:
                return True
            elif self.val == other.val:
                return True
            else:
                return False
        else:
            return self.val == other
    
    def eval(self) -> Term:
        return self._value


class ToType(Term):
    '''
    Construct a term as a function type
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, type : Term, para : Para, type_right : Term | Para):
        '''
        Construction of term: [para_env] -> type_right
        The 'para_env' should point to the ParaMicroEnv which contains the parameter for this function
        '''
        local_env = ParaMicroEnv(para)
        para.type.set_parent_env(local_env)
        type_right.set_parent_env(local_env)

        super().__init__(type, local_env)

        self._para_env : ParaMicroEnv = self._para_env
        self._type_right : Term | Para = type_right

    @property
    def para_env(self) -> ParaMicroEnv:
        return self._para_env
    
    @property
    def para(self) -> Para:
        if self._para_env.para is None:
            raise Exception("unexpected situation")
        return self._para_env.para
    
    @property
    def type_right(self) -> Term | Para:
        return self._type_right

    def __str__(self) -> str:
        return "(" + str(self.para) + " : " + str(self.para.type) + ") -> " + str(self._type_right)
        
    
    def __eq__(self, other) -> bool:
        '''
        we require that the equivalence check will consider different parameter naming
        '''
        if isinstance(other, ToType):

            '''
            check whether the two parameters paraA and paraB are the same, with respect to the two environments
            '''
            type_eq = self.para.type == other.para.type

            return type_eq and self.type_right == other.type_right

        else:
            raise NotImplemented

    def substitute(self, para: Para, val: Term | Para) -> Term:
        if self._type is None:
            raise Exception("unexpected situation")
        else:
            new_type = self._type.substitute(para, val)

        new_para = self.para.substitute(para, val)
        if isinstance(new_para, Term):
            # this should not happen, because parameter id are unique
            raise Exception("unexpected situation")

        new_term = ToType(new_type, new_para, self._type_right.substitute(para, val))
        new_term.set_parent_env(self._para_env)
        return new_term        


class Lambda(Term):
    '''
    Construct a term as an anonymous function
    '''
    def __init__(self, type : Term, input : Para, output : Term | Para):
        local_env = ParaMicroEnv(input)
        input.type.set_parent_env(local_env)
        output.set_parent_env(local_env)

        super().__init__(type, local_env)
        self._para_env : ParaMicroEnv = self._para_env
        self._output : Term | Para = output
    
    @property
    def para_env(self) -> ParaMicroEnv:
        return self._para_env

    @property
    def para(self) -> Para:
        if self._para_env.para is None:
            raise Exception("unexpected situation")
        return self._para_env.para

    def eval_on_val(self, val : Term | Para) -> Term:
        '''
        evaluate the output using 'val' as input
        WARNING : no type check
        '''

        result = self._output.substitute(self.para, val)
        if not isinstance(result, Term):
            raise Exception("unexpected situation")
        return result
    
    def __str__(self) -> str:
        return "fun(" + str(self.para) + " : " + str(self.para.type) + ") => " + str(self._output)
        
    def __eq__(self, other) -> bool:
        if isinstance(other, ToType):
            return False
        else:
            raise NotImplemented

    def substitute(self, para: Para, val: Term | Para) -> Term:
        if self._type is None:
            raise Exception("unexpected situation")
        else:
            new_type = self._type.substitute(para, val)

        new_para = self.para.substitute(para, val)
        if isinstance(new_para, Term):
            # this should not happen, because parameter id are unique
            raise Exception("unexpected situation")

        new_term = Lambda(new_type, new_para, self._output.substitute(para, val))
        return new_term


class Apply(Term):
    '''
    Construct a term as a function application
    Readonly. No copy needed in assignment.
    '''
    def __init__(self, type : Term, fun : Term, para : Term | Para):
        '''
        the type of fun should be a 'function'
        '''
        local_env = ParaMicroEnv()
        para.set_parent_env(local_env)
        fun.set_parent_env(local_env)

        super().__init__(type, local_env)

        self._para_env : ParaMicroEnv
        self._term_fun : Term = fun
        self._term_val : Term | Para = para

    @property
    def para_env(self) -> ParaMicroEnv:
        return self._para_env

    def __str__(self) -> str:
        return "(" + str(self._term_fun) + " " + str(self._term_val) + ")"

    def eval(self) -> Term:
        '''
        evaluate the application and return the result
        '''

        if self.para_env.parent is not None:
            raise DTS_RuntimeError("invalid function evaluation")
        
        elif isinstance(self._term_fun, Axiom):
            raise DTS_RuntimeError("Axiom '" + str(self._term_fun) + "' is not executable.")

        elif isinstance(self._term_fun, Var):
            # apply the substitution
            temp = Apply(self.type, self._term_fun.val, self._term_val)
            result = temp.eval()
            # set the parent environment to None
            result.set_parent_env(ParaMicroEnv())
            return result
        
        elif isinstance(self._term_fun, Lambda):
            result = self._term_fun.eval_on_val(self._term_val)
            # set the parent environment to None
            result.set_parent_env(ParaMicroEnv())
            return result
        
        else:
            raise Exception("unexpected situation")

    def __eq__(self, other) -> bool:
        return self.eval() == other

    def substitute(self, para: Para, val: Term | Para) -> Term:
        if self._type is None:
            raise Exception("unexpected situation")
        else:
            new_type = self._type.substitute(para, val)

        new_term_fun = self._term_fun.substitute(para, val)
        if not isinstance(new_term_fun, ToType):
            raise Exception("unexpected situation")

        new_term = Apply(new_type, new_term_fun, self._term_val.substitute(para, val))
        new_term.set_parent_env(self._para_env)
        return new_term
        


class TermFact:
    '''
    Apply the factory model. New instance checks are done here.
    '''

    __instance : TermFact | None = None
    __max_sort_level : int = 16

    def __new__(cls):
        if TermFact.__instance is not None:
            return TermFact.__instance

        instance = super().__new__(cls)
        #initialize a term factory

        if TermFact.__max_sort_level < 0:
            raise DTS_RuntimeError("Invalid maximum sort level.")

        # the list of all sorts, the index corresponds to the universe number
        instance._sort_list = [Sort(None, TermFact.__max_sort_level)]

        for u_num in range(TermFact.__max_sort_level-1, -1, -1):
            upper_sort = instance._sort_list[0]
            instance._sort_list.insert(0, Sort(upper_sort, u_num))
        
        TermFact.__instance = instance
        return instance

    def __init__(self):
        self._sort_list : List[Sort]

    # term construction methods
    def sort_term(self, u_num : int) -> Sort:
        return self._sort_list[u_num]

    def axiom(self, axiom_id : str, type : Term) -> Axiom:
        if not isinstance(axiom_id, str):
            raise DTS_RuntimeError("invalid axiom id")
        if not isinstance(type, Term):
            raise DTS_RuntimeError("invalid type")
        if not type.is_type:
            raise DTS_RuntimeError("The term '" + str(type) + "' is not a type.")
        
        return Axiom(axiom_id, type)

    def var(self, var_id : str, type : Term, value : Term) -> Var:
        '''
        variable should not contain free parameters
        '''
        if not isinstance(var_id, str):
            raise DTS_RuntimeError("invalid variable id")
        if not isinstance(type, Term):
            raise DTS_RuntimeError("invalid type")
        if not type.is_type:
            raise DTS_RuntimeError("The term '" + str(type) + "' is not a type.")
        if not isinstance(value, Term):
            raise DTS_RuntimeError("invalid value")
        # check whether the type and value corresponds
        if not value.type == type:
            raise DTS_RuntimeError("The value '" + str(value) + "' is not of type '" + str(type) + "'.")
        
        self.no_para_check(type)
        self.no_para_check(value)

        return Var(var_id, type, value)
    
    def _no_para_check_iter(self, term : Term | Para, para_env : ParaMicroEnv) -> None:
        if isinstance(term, Axiom) or isinstance(term, Sort) or isinstance(term, Var):
            return
        elif isinstance(term, Para):
            try:
                para_env.get_term(term.id)
                return
            except DTS_RuntimeError:
                raise DTS_RuntimeError("free parameter detected")
        elif isinstance(term, ToType):
            self._no_para_check_iter(term.para.type, para_env)
            self._no_para_check_iter(term.type, term.para_env)
            return
        elif isinstance(term, Lambda):
            self._no_para_check_iter(term.para.type, para_env)
            self._no_para_check_iter(term._output, term.para_env)
            return
        elif isinstance(term, Apply):
            self._no_para_check_iter(term._term_fun, term.para_env)
            self._no_para_check_iter(term._term_val, term.para_env)
            return
            
        raise Exception("unexpected situation")


    def no_para_check(self, term : Term) -> None:
        '''
        check that there is no free parameter in this term
        '''
        return self._no_para_check_iter(term, ParaMicroEnv())
    
    def _fun_con_type(self, type1 : Term | Para, type2 : Term | Para) -> Sort:
        '''
        get the type of function construction (a : type1) -> type2
        '''
        if not isinstance(type1.type, Sort) or not isinstance(type2.type, Sort):
            raise DTS_RuntimeError("type1 and type2 should be types")
        
        return self._sort_list[max(type1.type.u_num, type2.type.u_num)]

    def para(self,  para_id : str, type : Term) -> Para:
        if not isinstance(para_id, str):
            raise DTS_RuntimeError("invalid parameter id")
        if not isinstance(type, Term):
            raise DTS_RuntimeError("invalid type")
        if not type.is_type:
            raise DTS_RuntimeError("The term '" + str(type) + "' is not a type.")
        return Para(para_id, type)

    def to_type(self, para : Para, type_right : Term | Para) -> ToType:
        if not isinstance(para, Para):
            raise DTS_RuntimeError("invalid parameter")
        if not isinstance(type_right, Term) and not isinstance(type_right, Para):
            raise DTS_RuntimeError("invalid right type")
        if not type_right.is_type:
            raise DTS_RuntimeError("The right type term '" + str(type_right) + "' is not a type.")

        if para is None:
            raise DTS_RuntimeError("The environment should not be empty")

        # evaluate the type
        type = self._fun_con_type(para.type, type_right)

        # copy the para_env to avoid unexpected manipulations
        return ToType(type, para, type_right)    

    def _lambda_type(self, input : Para, output: Term) -> Term:
        '''
        get the type of a lambda expression
        '''
        return self.to_type(input, output.type)

    def fun_lambda(self, input : Para, output : Term | Para) -> Lambda:
        if not isinstance(input, Para):
            raise DTS_RuntimeError("invalid lambda parameter")
        if not isinstance(output, Term) and not isinstance(output, Para):
            raise DTS_RuntimeError("invalid output for lambda expression")

        return Lambda(self.to_type(input, output.type), input, output)


    def fun_apply(self, fun : Term, value : Term | Para) -> Apply:
        if not isinstance(fun.type, ToType):
            raise DTS_RuntimeError("The term '" + str(fun) + "' is not a function." )
        
        if not isinstance(value, Term) and not isinstance(value, Para):
            raise DTS_RuntimeError("The value parameter to apply is neither a parameter nor a term.")

        type_needed = fun.type.para.type
        if not type_needed == value.type:
            raise DTS_RuntimeError("The value parameter '" + str(value) + "' of type '" + str(fun.type.para.type) + 
                "cannot be applied here, where a value of type '" + str(type_needed) + "' is needed.")
        
        # calculate the type
        apply_type = fun.type.type_right.substitute(fun.type.para, value)
        if isinstance(apply_type, Para):
            raise Exception("unexpected situation")
        
        return Apply(apply_type, fun, value)

    def fun_evl(self, fun : ToType, value : Term) -> Term:
        '''
        substitue the parameter, evaluate and return the result
        the evaluation happens at the fun_apply structures
        '''
        temp_fun_apply = self.fun_apply(fun, value)
        return temp_fun_apply.eval()
    
    def eval(self, term : Term) -> Term:
        if isinstance(term, Var):
            return term.val
        elif isinstance(term, Apply):
            return term.eval()
        else:
            return term





