"""
Copyright 2013 Steven Diamond

This file is part of CVXPY.

CVXPY is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CVXPY is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CVXPY.  If not, see <http://www.gnu.org/licenses/>.
"""

from .. import settings as s
from .. import utilities as u
from .. import interface as intf
from ..constraints.affine import AffEqConstraint
import types
from collections import deque

class AffObjective(u.Affine):
    """ An affine objective. The result of canonicalization. """
    # variables - a list of variables.
    # terms - a list of multiplication queues.
    # shape - an object representing the dimensions.
    def __init__(self, variables, terms, shape):
        self._vars = variables
        self._terms = terms
        self._shape = shape
        super(AffObjective, self).__init__()

    def name(self):
        return str(self._terms)

    def __str__(self):
        return self.name()

    def __repr__(self):
        return self.name()

    # The dimensions of the objective.
    @property
    def size(self):
        return self._shape.size

    # Returns a dict of term id to coefficient.
    # interface - the matrix interface to convert constants
    #             into a matrix of the target class.
    def coefficients(self, interface):
        final_coeffs = {}
        for mults in self._terms:
            root = mults[0]
            root_coeffs = root.coefficients(interface)
            for id,coeff in root_coeffs.items():
                coefficient = self.dequeue_mults(coeff, mults, interface)
                if id in final_coeffs:
                    final_coeffs[id] = final_coeffs[id] + coefficient
                else:
                    final_coeffs[id] = coefficient
        return final_coeffs

    # Resolves a multiplication stack into a single coefficient.
    @staticmethod
    def dequeue_mults(coefficient, mults, interface):
        for i in range(len(mults)-1):
            lh = mults[i+1]
            # Only contains a constant coefficient.
            lh_coeff = lh.coefficients(interface).values()[0]
            coefficient = lh_coeff * coefficient
        return coefficient

    # Returns a list of variables.
    def variables(self):
        return self._vars

    # Multiplies by a ones matrix to promote a scalar coefficient.
    @staticmethod
    def promote(obj, shape):
        ones = types.constant()(intf.DEFAULT_INTERFACE.ones(*shape.size))
        ones_obj,dummy = ones.canonical_form()
        return ones_obj*obj

    # Concatenates the terms.
    # Multiplies by a ones matrix if promotion occurs.
    def __add__(self, other):
        new_shape = self._shape + other._shape
        if new_shape.size > self._shape.size:
            self = self.promote(self, new_shape)
        elif new_shape.size > other._shape.size:
            other = self.promote(other, new_shape)
        return AffObjective(self.variables() + other.variables(),
                            self._terms + other._terms,
                            new_shape)

    def __sub__(self, other):
        return self + -other

    # Distributes multiplications by left hand terms
    # across right hand terms.
    def __mul__(self, other):
        terms = AffObjective.mul_terms(self._terms, other._terms)
        return AffObjective(other.variables(), terms, 
                            self._shape * other._shape)

    # Multiplies every term by -1.
    def __neg__(self):
        lh_mult = deque([types.constant()(-1)])
        terms = AffObjective.mul_terms([lh_mult], self._terms)
        return AffObjective(self.variables(), terms, self._shape)

    # Utility function for multiplying lists of terms.
    @staticmethod
    def mul_terms(lh_terms, rh_terms):
        terms = []
        for lh_mult in lh_terms:
            for rh_mult in rh_terms:
                mult = deque(rh_mult)
                mult.extend(lh_mult)
                terms.append(mult)
        return terms


    # Returns an (AffineObjective, [AffineConstraints]) tuple
    # representing the tranpose.
    @property
    def T(self):
        A = types.variable()(*self.size)
        obj = A.T.canonical_form()[0]
        return (obj, [AffEqConstraint(A, self)])

    # # Returns an (AffineObjective, [AffineConstraints]) tuple.
    # # Examines every term. If the mult deque has one element, that
    # # element is set to its transpose and the term is kept.
    # # If the mult deque has more than one element, it is collected in
    # # an AffineEquality of the form X.T == terms. The final objective is
    # # the kept terms and X.
    # @property
    # def T(self):
    #     transpose_terms = []
    #     equality_terms = []
    #     for mults in self._terms:
    #         if len(mults) == 1: # Transpose the term.
    #             elem = mults[0]
    #             transpose_terms.append(deque([elem.T]))
    #         else: # Move the term to the equality.
    #             equality_terms.append(mults)
    #     # Create a new variable for the equality terms.
    #     vars = self.variables_from_terms(transpose_terms)
    #     new_obj = AffObjective(vars, transpose_terms, u.Shape(self.size[1],self.size[0]))
    #     if len(equality_terms) > 0:
    #         x = types.variable()(*self.size)
    #         x_obj = x.canonical_form()[0]
    #         vars = self.variables_from_terms(equality_terms)
    #         eq_obj = AffObjective(vars, equality_terms, self._shape)
    #         constraints = [AffEqConstraint(x.T, eq_obj)]
    #         return (new_obj + x_obj, constraints)
    #     else: # No new variables needed.
    #         return (new_obj, [])

    # # Extract a variables list from a list of terms.
    # @staticmethod
    # def variables_from_terms(terms):
    #     variables = []
    #     for mults in terms:
    #         variables += mults[0].variables()
    #     return variables