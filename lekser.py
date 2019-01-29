import ply.lex as lex

tokens = (
	'DECLARE', 'IN', 'END','SEMICOLON',			# 0 program
	'NUM', 										# 1 liczby
	'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD',		# 2 operatory
	'EQ', 'NEQ', 'LEQ', 'GEQ', 'LT', 'GT',		# 3 relacje
	'ASSIGN',									# 4 przypisania
	'LBR','RBR','COLON',						# 5 tablice
	'IF', 'THEN', 'ELSE', 'ENDIF',				# 6 warunki IF
	'DO',										# 7 petle
		'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',	# 7a FOR
		'WHILE', 'ENDDO', 'ENDWHILE',				# 7b WHILE
	'READ', 'WRITE', 							# 8 odczyt zapis
	'ID'										# 9 identyfikatory
)

# 0 PROGRAM
t_ignore_COM = r'\[[^\]]*\]'
t_DECLARE	= r'DECLARE'
t_IN		= r'IN'
t_END		= r'END'
t_SEMICOLON	= r';'

# 1 LICZBY
def t_NUM(t):
	r'\d+'
	t.value = int(t.value)	
	return t

# 2 OPERATORY
t_PLUS	= r'\+'
t_MINUS	= r'\-'
t_MULT	= r'\*'
t_DIV	= r'\/'
t_MOD	= r'\%'

# 3 RELACJE
t_EQ	= r'='
t_NEQ	= r'!='
t_LEQ	= r'<='
t_GEQ	= r'>='
t_LT	= r'<'
t_GT	= r'>'

# 4 PRZYPISANIA
t_ASSIGN = r':='

# 5 TABLICE
t_LBR	= r'\('
t_RBR	= r'\)'
t_COLON		= r':'

# 6 WARUNKI IF
t_IF	= r'IF'
t_THEN	= r'THEN'
t_ELSE	= r'ELSE'
t_ENDIF	= r'ENDIF'

# 7 PETLE
t_DO		= r'DO'
t_FOR		= r'FOR'
t_FROM		= r'FROM'
t_TO		= r'TO'
t_DOWNTO	= r'DOWNTO'
t_ENDFOR	= r'ENDFOR'
t_WHILE		= r'WHILE'
t_ENDDO		= r'ENDDO'
t_ENDWHILE	= r'ENDWHILE'

# 8 ODCZYT ZAPIS
t_READ	= r'READ'
t_WRITE	= r'WRITE'

# 9 IDENTYFIKATORY
t_ID = r'[_a-z]+'

# Define a rule so we can track line NUMs
def t_newline(t):
	r'\r?\n+'
	t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()