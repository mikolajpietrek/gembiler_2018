import sys
import ply.yacc as yacc
from lekser import tokens
import re

memory_count = 1
variables={}
inits={}
arrays={}
labels_val=[]


############ CZĘŚĆ I - MOJE FUNKCJE POMOCNICZE #################

## DEBUGOWANIE ##

debug = 0

def begin(str):
	if debug == 1:
		return "##BEGIN " + str + "\n"
	else:
		return ""
		
def end(str):
	if debug == 1:
		return "##END " + str + "\n"	
	else:
		return ""		

		
## TWORZENIE ZMIENNYCH, STAŁYCH, TABLIC ##

def generate_const(num, register):
	list = ""
	while num != 0:
		if num % 2 == 0:
			num = num // 2
			list = "ADD " + register + " " + register + "\n" + list
		else:
			num = num - 1
			list = "INC " + register + "\n" + list
	list = "SUB " + register + " " + register + "\n" + list 
	return list
	
def add_array(id, start, stop, lineno):
	if stop<start:
		raise Exception("Błąd w linii " + lineno + ': Niewłaściwy zakres tablicy ' + id)
	global memory_count
	position = memory_count + 1
	arrays[id]=(position,start,stop)
	memory_count += (stop-start + 1)

def add_variable(id, lineno):
	if id in variables:
		raise Exception("Błąd w linii " + lineno + ': Druga deklaracja ' + id)
	global memory_count
	memory_count += 1
	variables[id] = memory_count

def del_variable(id):
	variables.pop(id)
		
def add_temp_variable():
	global memory_count
	temp_var_name = "$T" + str(memory_count)
	add_variable(temp_var_name, None)
	inits[temp_var_name] = True
	return temp_var_name
	
	
## SZUKANIE W PAMIĘCI ##

def get_var_index(var_name, lineno):
	if var_name not in variables:
		raise Exception('Variable error!')
	else:
		return variables[var_name]

def get_tab_data(tab_name):
	if tab_name not in arrays:
		raise Exception('Variable error!')
	else:
		return arrays[tab_name]
	
	
## OBSŁUGA PAMIĘCI ##

def load_value_addr(value, lineno):
	if value[0] == "id":
		check_variable_address(value[1], lineno)
		return	begin("LOAD_VAR_ADDR") +\
				generate_const(variables[value[1]], "A") +\
				end("LOAD_VAR_ADDR") 
	elif value[0] == "tab":
		check_array_address(value[1], lineno)
		tab_pos, tab_start, tab_stop = arrays[value[1]]
		cell_index = value[2]
		return	begin("LOAD_TAB_ADDR") +\
				load_value(cell_index,"A", lineno) +\
				generate_const(tab_start, "C") +\
				"SUB A C" + "\n" +\
				generate_const(tab_pos, "C") +\
				"ADD A C" + "\n" +\
				end("LOAD_TAB_ADDR") 
	else:
		raise Exception('To się nie miało prawa wykonać... '+ str(value))

def load_value(value,register,lineno):
	if value[0] == "num":
		return	begin("LOAD_CONST") +\
				generate_const(int(value[1]),register) +\
				end("LOAD_CONST")
	if value[0] == "id":
		check_variable_initialization(value[1], lineno)
	return	begin("LOAD_VAR") +\
			load_value_addr(value, lineno) +\
			"LOAD " + register + "\n" +\
			end("LOAD_VAR") 

			
## PRZETWARZANIE ETYKIET ##
	
def add_multi_labels(count):
	t_labels=[]
	t_jumps=[]
	for i in range(0,count):
		labels_val.append(-1)	
		num = str(len(labels_val)-1)
		t_labels.append("#L" + num + "#")
		t_jumps.append("#J" + num + "#")
	return (t_labels, t_jumps)
	
def remove_labels(program):
	line_num=0
	removed_labels = []
	for line in program.split("\n"):
		match = re.search("#L[0-9]+#", line)
		if match is not None:
			label_id = int(match.group()[2:-1])
			labels_val[label_id] = line_num
			line = re.sub("#L[0-9]+#", "", line)
		removed_labels.append(line)
		line_num += 1
	
	removed_jumps = ""
	for line in removed_labels:
		match = re.search("#J[0-9]+#", line)
		if match is not None:
			jump_id = int(match.group()[2:-1])
			jump_line = labels_val[jump_id]
			line = re.sub("#J[0-9]+#", str(jump_line), line)
		removed_jumps += line + "\n"
	return removed_jumps
	
	
############ CZĘŚĆ II - SCHEMAT PROGRAMU #################
	
## PROGRAM I KOMENDY
	
def p_program(p):
	'''program : DECLARE declarations IN commands END'''
	p[0] = remove_labels(p[4] + "HALT") 
	
## DEKLARACJE ZMIENNYCH
	
def p_declarations_variable(p):
	'''declarations	: declarations ID SEMICOLON '''
	id, lineno = p[2],str(p.lineno(2))	
	add_variable(id, lineno)


def p_declarations_array(p):
	'''declarations	: declarations ID LBR NUM COLON NUM RBR SEMICOLON '''
	id, start, stop, lineno = p[2], p[4], p[6], str(p.lineno(2))
	add_array(id, start, stop, lineno)

def p_declarations_empty(p):
	'''declarations	: '''
	
## KOMENDY

def p_commands_mult(p):
	'''commands	: commands command '''
	p[0] =	p[1] + p[2]
	
def p_commands_one(p):
	'''commands	: command'''
	p[0] = p[1]
	
	
############ CZĘŚĆ III - WŁAŚCIWY KOMPILATOR #################
	
			
## PRZYPISANIA	
				
def p_command_assign(p):
	'''command	: identifier ASSIGN expression SEMICOLON '''
	# expression zwraca wartość w rejestrze B, generuję adres zmiennej w A, ładuję wartość B do pamięci na adres A
	identifier, expression, lineno = p[1], p[3], str(p.lineno(1)) 
	p[0] =	begin("ASSIGN") +\
			expression +\
			load_value_addr(identifier, lineno) +\
			"STORE B\n" +\
			end("ASSIGN")
	inits[identifier[1]] = True
				
def p_command_if(p):
	'''command	: IF condition THEN commands ENDIF'''
	condition, commands_if, lineno = p[2], p[4], str(p.lineno(1)) 
	p[0] =	begin("IF") +\
			condition[0] +\
			commands_if +\
			condition[1] +\
			end("IF")
def p_command_if_else(p):
	'''command	: IF condition THEN commands ELSE commands ENDIF'''			
	condition, commands_if, commands_else, lineno = p[2], p[4], p[6], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(1)
	p[0] =	begin("IF_ELSE") +\
			condition[0] +\
			commands_if +\
			"JUMP " + jumps[0] + "\n" +\
			condition[1] +\
			commands_else +\
			labels[0] +\
			end("IF_ELSE")
		
	
## PĘTLE
	
def p_command_while(p):
	'''command	: WHILE condition DO commands ENDWHILE'''
	labels, jumps = add_multi_labels(1)
	condition, commands, lineno = p[2], p[4], str(p.lineno(1)) 
	p[0] =	begin("WHILE") +\
			labels[0] +\
			condition[0] +\
			commands +\
			"JUMP " + jumps[0] + "\n" +\
			condition[1] +\
			end("WHILE")
				
def p_command_dowhile(p):
	'''command	: DO commands WHILE condition ENDDO '''
	labels, jumps = add_multi_labels(1)
	commands, condition, lineno = p[2], p[4], str(p.lineno(1)) 
	p[0] =	begin("DOWHILE") +\
			labels[0] +\
			commands +\
			condition[0] +\
			"JUMP " + jumps[0] + "\n" +\
			condition[1] +\
			end("DOWHILE")
				
def p_iterator(p):
	'''iterator	: ID '''	
	id, lineno = p[1], str(p.lineno(1)) 
	p[0] = id
	add_variable(id, lineno)
	inits[id] = True
	
def p_command_for_to(p):
	'''command	: FOR iterator FROM value TO value DO commands ENDFOR '''
	labels, jumps = add_multi_labels(3)
	temp_var = add_temp_variable()
	iterator, start_val, stop_val, commands, lineno = p[2], p[4], p[6], p[8], str(p.lineno(1)) 
			# w tym momencie mam w pamięci iterator H oraz stop temp-var G 
			
			
	p[0] =	begin("FOR") +\
			load_value(stop_val,"G", lineno) +\
			load_value_addr(("id",temp_var), lineno) +\
			"STORE G\n" +\
			load_value(start_val,"H", lineno) +\
			load_value_addr(("id",iterator), lineno) +\
			"STORE H\n" +\
			labels[2] +\
			load_value(("id",temp_var),"G", lineno) +\
			load_value(("id", iterator),"H", lineno) +\
			"SUB H G\n" +\
			"JZERO H " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			labels[0] + commands +\
			load_value(("id",iterator),"H", lineno) +\
			"INC H\n" +\
			load_value_addr(("id",iterator), lineno) +\
			"STORE H\n" +\
			"JUMP " + jumps[2] + "\n" +\
			labels[1] +\
			end("FOR")

	del_variable(iterator)
	
def p_command_for_downto(p):
	'''command	: FOR iterator FROM value DOWNTO value DO commands ENDFOR '''
	labels, jumps = add_multi_labels(3)
	iterator, start_val, stop_val, commands, lineno = p[2], p[4], p[6], p[8], str(p.lineno(1)) 
	temp_var = add_temp_variable()
			# w tym momencie mam w pamięci iterator H oraz stop temp-var G 
	p[0] =	begin("FOR") +\
			load_value(stop_val,"G", lineno) +\
			load_value_addr(("id",temp_var), lineno) +\
			"STORE G\n" +\
			load_value(start_val,"H", lineno) +\
			load_value_addr(("id",iterator), lineno) +\
			"STORE H\n" +\
			labels[2] +\
			load_value(("id",temp_var),"G", lineno) +\
			load_value(("id", iterator),"H", lineno) +\
			"SUB G H\n" +\
			"JZERO G " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			labels[0] + commands +\
			load_value(("id",iterator),"H", lineno) +\
			load_value_addr(("id",iterator), lineno) +\
			"JZERO H " + jumps[1] + "\n" +\
			"DEC H\n" +\
			"STORE H\n" +\
			"JUMP " + jumps[2] + "\n" +\
			labels[1] +\
			end("FOR")

	del_variable(iterator)

	
## WEJŚCIE WYJŚCIE
	
def p_command_input(p):
	'''command	: READ identifier SEMICOLON '''
	#adres zmiennej generuję w rejestrze A, ładuję z konsoli do pamięci do rejestru B, zapisuję z rejestru B pod adres z A
	identifier, lineno = p[2], str(p.lineno(1)) 
	inits[identifier[1]] = True
	p[0] =	begin("READ") +\
			load_value_addr(identifier, lineno) +\
			"GET B\n" +\
			"STORE B\n" +\
			end("READ")

def p_command_output(p):
	'''command	: WRITE value SEMICOLON '''	
	value, lineno = p[2], str(p.lineno(1)) 	
	#wyświetlam B w konsoli 
	p[0] =	begin("WRITE") +\
			load_value(value,"B", lineno) +\
			"PUT B\n"  +\
			end("WRITE")	
		
		
## WARTOŚCI PROSTE I ARYTMETYKA
	
def p_expression_value(p):
	'''expression : value'''
	value, lineno = p[1], str(p.lineno(1)) 	
	p[0] =	begin("SIMPLE_EXP") +\
			load_value(value,"B", lineno) +\
			end("SIMPLE_EXP")

def p_expression_plus(p):
	'''expression : value PLUS value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	p[0] =	begin("PLUS") +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"ADD B C\n" +\
			end("PLUS")
	
def p_expression_minus(p):
	'''expression : value MINUS value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	p[0] =	begin("MINUS") +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"SUB B C\n" +\
			end("MINUS")
	
def p_expression_mult(p):
	'''expression : value MULT value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(4)
	p[0] =	begin("MULT")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"SUB D D\n" +\
			"" + labels[3] + "JZERO B " + jumps[2] + "\n" +\
			"JODD B " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			"" + labels[0] + "ADD D C\n" +\
			"" + labels[1] + "HALF B\n" +\
			"ADD C C\n" +\
			"JUMP " + jumps[3] + "\n" +\
			"" + labels[2] + "COPY B D\n" +\
			end("MULT")
	
def p_expression_div(p):
	'''expression : value DIV value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(7)
	
	p[0] = 	begin("DIV")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"JZERO C " + jumps[6] + "\n" +\
			"SUB D D\n" +\
			"INC D\n" +\
			"" + labels[0] + "COPY A B\n" +\
			"SUB A C\n" +\
			"JZERO A " + jumps[1] + "\n" +\
			"ADD C C\n" +\
			"ADD D D\n" +\
			"JUMP " + jumps[0] + "\n" +\
			"" + labels[1] + "COPY E B\n" +\
			"SUB B B\n" +\
			"" + labels[2] + "COPY A C\n" +\
			"SUB A E\n" +\
			"JZERO A " + jumps[5] + "\n" +\
			"JUMP " + jumps[3] + "\n" +\
			"" + labels[5] + "SUB E C\n" +\
			"ADD B D\n" +\
			"" + labels[3] + "HALF C\n" +\
			"HALF D\n" +\
			"JZERO D " + jumps[4] + "\n" +\
			"JUMP " + jumps[2] + "\n" +\
			"" + labels[6] + "SUB B B\n" +\
			labels[4] +\
			end("DIV") 
			#div w B
	
def p_expression_mod(p):
	'''expression : value MOD value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(7)
	
	p[0] = 	begin("MOD")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"JZERO C " + jumps[6] + "\n" +\
			"SUB D D\n" +\
			"INC D\n" +\
			"" + labels[0] + "COPY A B\n" +\
			"SUB A C\n" +\
			"JZERO A " + jumps[1] + "\n" +\
			"ADD C C\n" +\
			"ADD D D\n" +\
			"JUMP " + jumps[0] + "\n" +\
			"" + labels[1] + "COPY E B\n" +\
			"SUB B B\n" +\
			"" + labels[2] + "COPY A C\n" +\
			"SUB A E\n" +\
			"JZERO A " + jumps[5] + "\n" +\
			"JUMP " + jumps[3] + "\n" +\
			"" + labels[5] + "SUB E C\n" +\
			"ADD B D\n" +\
			"" + labels[3] + "HALF C\n" +\
			"HALF D\n" +\
			"JZERO D " + jumps[4] + "\n" +\
			"JUMP " + jumps[2] + "\n" +\
			"" + labels[6] + "SUB B B\n" +\
			"" + labels[4] + "COPY B E\n" +\
			end("MOD") 
			#MOD w B
	
## WARUNKI

# condition jest tylko we WHILE oraz IF, chyba mogę tutaj ładować
	
def p_condition_eq(p):
	'''condition	: value EQ value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(3)
	p[0] =	(begin("EQ1")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"COPY D B\n" +\
			"SUB D C\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			"JUMP " + jumps[2] + "\n" +\
			"" + labels[0] + "COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[1] + "\n" +\
			"JUMP " + jumps[2] + "\n" +\
			labels[1] +\
			end("EQ1"),
			begin("EQ2") +\
			labels[2] +\
			end("EQ2"))
	
	
def p_condition_neq(p):
	'''condition	: value NEQ value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(3)
	p[0] =	(begin("NEQ1")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"COPY D B\n" +\
			"SUB D C\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			"" + labels[0] + "COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[2] + "\n" +\
			labels[1] +\
			end("NEQ1"),
			begin("NEQ2") +\
			labels[2] +\
			end("NEQ2"))
	
	
def p_condition_lt(p):
	'''condition	: value LT value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(1)
	p[0] =	(begin("LT1")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			end("LT1"),
			begin("LT2") +\
			labels[0] +\
			end("LT2") )	
			
def p_condition_gt(p):
	'''condition	: value GT value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(1)
	p[0] =	(begin("GT1")  +\
			load_value(value2, "B", lineno) +\
			load_value(value1, "C", lineno) +\
			"COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			end("GT1"),
			begin("GT2") +\
			labels[0] +\
			end("GT2") )		
	 
def p_condition_leq(p):
	'''condition	: value LEQ value'''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(2)
	p[0] =	(begin("LEQ1")  +\
			load_value(value2, "B", lineno) +\
			load_value(value1, "C", lineno) +\
			"COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			end("LEQ1") + labels[0],
			begin("LEQ2") +\
			labels[1] +\
			end("LEQ2") )
	
def p_condition_geq(p):
	'''condition	: value GEQ value '''
	value1, value2, lineno = p[1], p[3], str(p.lineno(1)) 	
	labels, jumps = add_multi_labels(2)
	p[0] =	(begin("GEQ1")  +\
			load_value(value1, "B", lineno) +\
			load_value(value2, "C", lineno) +\
			"COPY D C\n" +\
			"SUB D B\n" +\
			"JZERO D " + jumps[0] + "\n" +\
			"JUMP " + jumps[1] + "\n" +\
			end("GEQ1") + labels[0],
			begin("GEQ2") +\
			labels[1] +\
			end("GEQ2") )
	
		

############ CZĘŚĆ IV - ROZRÓŻNIANIE IDENTYFIKATORÓW #################
	

## ZMIENNE

def p_value_NUM(p): 
	'''value : NUM '''
	p[0] = ("num",p[1])
	
def p_value_identifier(p):
	'''value : identifier '''
	p[0] = (p[1])
	
## IDENTYFIKATORY
	
def p_identifier_id(p):
	'''identifier	: ID '''
	p[0] = ("id",p[1])

def p_identifier_tab_id(p):
	'''identifier	: ID LBR ID RBR '''
	p[0] = ("tab",p[1],("id",p[3]))

def p_identifier(p):
	'''identifier	: ID LBR NUM RBR '''
	p[0] = ("tab",p[1],("num",p[3]))
	
	
############ CZĘŚĆ V - BŁĘDY #################
	
	
def p_error(p):
	raise Exception("Błąd w linii " + str(p.lineno) + ': nierozpoznany napis ' + str(p.value)) 

def check_array_address(id, lineno):
	if id not in arrays:
		if id in variables:
			raise Exception("Błąd w linii " + lineno + ': niewłaściwe użycie zmiennej ' + id)
		else:
			raise Exception("Błąd w linii " + lineno + ': niewłaściwe użycie zmiennej tablicowej ' + id)	

def check_variable_address(id, lineno):
	if id not in variables:
		if id in arrays:
			raise Exception("Błąd w linii " + lineno + ': niewłaściwe użycie zmiennej tablicowej ' + id)
		else:
			raise Exception("Błąd w linii " + lineno + ': niezadeklarowana zmienna ' + str(id))	

def check_variable_initialization(id, lineno):
	if id not in inits:
		raise Exception("Błąd w linii " + lineno + ': użycie niezainicjowanej zmiennej ' + id)
	
############ CZĘŚĆ VI - TEST PARSERA #################


parser = yacc.yacc()
f=open(sys.argv[1], "r")
try:
	#print("A")
	parsed = parser.parse(f.read(),tracking=True)
except Exception as e:
	print(e)
	exit()
fw=open(sys.argv[2], "w")
fw.write(parsed)