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

from ..base_matrix_interface import BaseMatrixInterface
import cvxopt
import numbers

class DenseMatrixInterface(BaseMatrixInterface):
    """ 
    An interface to convert constant values to the cvxopt dense matrix class. 
    """
    TARGET_MATRIX = cvxopt.matrix
    # Convert an arbitrary value into a matrix of type self.target_matrix.
    @BaseMatrixInterface.scalar_const
    def const_to_matrix(self, value):
        return cvxopt.matrix(value, tc='d')

    # Return an identity matrix.
    def identity(self, size):
        matrix = self.zeros(size, size)
        for i in range(size):
            matrix[i,i] = 1
        return matrix

    # Return the dimensions of the matrix.
    def size(self, matrix):
        return matrix.size

    # Get the value of the passed matrix, interpreted as a scalar.
    def scalar_value(self, matrix):
        return matrix[0,0]

    # A matrix with all entries equal to the given scalar value.
    def scalar_matrix(self, value, rows, cols):
        return cvxopt.matrix(value, (rows,cols), tc='d')

    # Stuff the matrix into a different shape.
    # First convert the matrix to a cvxopt dense matrix.
    def reshape(self, matrix, size):
        matrix = self.const_to_matrix(matrix)
        return cvxopt.matrix(list(matrix), size, tc='d')