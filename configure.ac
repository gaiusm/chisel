AC_INIT([chisel], [4.0], [bug-automake@gnu.org])
AM_INIT_AUTOMAKE([-Wall -Wno-portability])
AM_PATH_PYTHON([3.0],, [:])
AM_CONDITIONAL([HAVE_PYTHON], [test "$PYTHON" != :])

AC_PROG_AWK
AC_PROG_CPP
AC_PROG_CXX
AC_PROG_INSTALL
AC_PROG_LN_S
AC_PROG_MAKE_SET

AC_CONFIG_SRCDIR([version.c])
AC_CONFIG_MACRO_DIR([m4])

AM_PATH_PYTHON

AS_MKDIR_P(m2)
AS_MKDIR_P(python)
AS_MKDIR_P(random)

dnl create these files
AC_CONFIG_FILES([Makefile m2/Makefile shell/pen2map shell/txt2pen random/Makefile])

AC_OUTPUT
