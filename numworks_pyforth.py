# NumWorks calculator Forth

#import readline


data_stack = []
return_stack = []
run = True

FORTH_FALSE = 0
FORTH_TRUE = 1  # or any non zero value


# Primitive Words

def clear_data_stack():
    global data_stack
    data_stack = []


def display_data_stack():
    print("stack: {} ({})".format(data_stack, len(data_stack)))
    print("     tos^\n")


def print_tos_and_remove():
    print(data_stack.pop())


def plus():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)
    data_stack.insert(0, next + tos)


def minus():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)
    data_stack.insert(0, next - tos)


def multiply():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)
    data_stack.insert(0, next * tos)


def divide():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)
    # we only want int results so use int()
    data_stack.insert(0, int(next / tos))


def greater_than():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)

    if next > tos:
        data_stack.insert(0, FORTH_TRUE)
    else:
        data_stack.insert(0, FORTH_FALSE)


def less_than():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)

    if next < tos:
        data_stack.insert(0, FORTH_TRUE)
    else:
        data_stack.insert(0, FORTH_FALSE)


def equal_to():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)

    if next == tos:
        data_stack.insert(0, FORTH_TRUE)
    else:
        data_stack.insert(0, FORTH_FALSE)


def dup():
    data_stack.insert(0, data_stack[0])


def swap():
    tos = data_stack.pop(0)
    next = data_stack.pop(0)
    data_stack.insert(0, tos)
    data_stack.insert(0, next)


def drop():
    data_stack.pop(0)


def display_words():
    for key, value in word_dict.items():
        print("\"{}\"\t\t{}".format(key, value))



word_dict = {
    # arithmetic
    '+': plus,
    '-': minus,
    '*': multiply,
    '/': divide,

    # relational
    '>': greater_than,
    '<': less_than,
    '=': equal_to,


    # stack related
    '.': print_tos_and_remove,
    '.s': display_data_stack,
    'clear': clear_data_stack,
    'dup': dup,
    'swap': swap,
    'drop': drop,

    'words': display_words,

    # # compile time only words
    # not needed in dict appart from being able to print out with 'words'
    'begin': "Compile time word only.",
    'again': "Compile time word only.",
    'until': "Compile time word only.",

    'if': "Compile time word only.",
    'else': "Compile time word only.",
    'then': "Compile time word only.",
}


def do_word(word):
    """Do word and return True. Return False if not in dict."""
    try:
        # some works, like begin, need the token list as well, most ignore it
        word_dict[word]()
        return True
    except KeyError:
        return False


def common_word_code(tokens):
    """Code common to all new words, Refactored out from add_word_to dict function."""

    # To implement compile time words that work in pairs such as 'if' 'else' 'then' or
    # 'begin' 'until' etc we need access to the index that is iterating through the tokens
    # list as we need to control of this to jump around to different words, so we use a
    # while loop as it uses a variable as an index, in this case variable i.

    global data_stack
    global return_stack
    ds_original_state = data_stack

    i = 0
    while i < len(tokens):
        try:
            # assume token is an int, and push on tos
            integer = int(tokens[i])
            data_stack.insert(0, integer)
        except ValueError:
            # token was not an int, so must be a word - try running it

            # Handle compile time words
            # in each case, we set i (either just increment it for the normal progress of
            # the loop or set it to another value) and then continue back to beginning of while.
            if tokens[i] == "begin":
                return_stack.insert(0, i + 1)
                i += 1
                continue
            elif tokens[i] == "again":
                i = return_stack[0]  # leave it on the return_stack for next time
                continue
            elif tokens[i] == "until":
                tos = data_stack.pop(0)
                if tos == FORTH_FALSE:
                    i = return_stack[0]
                    continue
                else:
                    return_stack.pop(0)
                    i += 1
                    continue

            elif tokens[i] == "if":
                # Do we do 'if' ?
                tos = data_stack.pop(0)
                if tos == FORTH_FALSE:
                    # No dont' do if. So skip to the first word after
                    # 'else' (if it exists) or 'then'
                    try:
                        i = tokens.index('else') + 1
                    except ValueError:
                        i = tokens.index('then') + 1

                    continue

                if tos == FORTH_TRUE:
                    # Yes, do if. So set i to first word after if and continue.
                    # As we are doing if, we will come to the else word if it was in tokens (not
                    # not the case when we are not doing if) so we need to handle the else word.
                    # we do that in another case statement see below:
                    i += 1
                    continue

            elif tokens[i] == "else":
                # We only see this word if we did the if block, so all we need to do is
                # set i to the word after 'then'
                i = tokens.index('then') + 1
                continue

            elif tokens[i] == 'then':
                # we need to just ignore this as it has served its purpose - as a marker in the
                # token list for the 'if' and  'else' word implementations
                # So just increment i and continue
                i += 1
                continue

            else:
                pass


            # Handle immediate mode words
            if do_word(tokens[i]):
                pass  # do_word() return True, so word exists and was run
            else:
                print("Error: The word '{}' is not defined!".format(tokens[i]))
                data_stack = ds_original_state
                return - 1 # or could I raise an error caught by parent function?

        i += 1



def add_word_to_dict(tokens):
    # remove colon and discard
    tokens.pop(0)
    new_word = tokens.pop(0)

    # Tokens is actually the definition of the compiled word, ie a list of words / numbers to
    # be run in sequence. Tokens is a list of strings and is saved in the closure env. of the
    # created function for this new compiled word.

    # create a function for this new compiled word
    def func():
        common_word_code(tokens)


    word_dict[new_word] = func


def get_input():
    """Return user input.

    - Return one line if in immediate mode (colon is NOT first char of line)
    - Or, return text up to ';' delimiter in compile mode (colon is first char of string)
    """
    buff = input('--> ')
    buff += " "  # add a space between lines

    if buff[0] == ":":
        # compile mode, get text up to ';' end delimeter
        if ';' in buff:
            buff =  buff.split(';')[0]
        else:
            at_end = False
            while not at_end:
                buff += input('--> ')
                buff += " "  # add a space between lines
                if ';' in buff:
                    buff = buff.split(';')[0]
                    at_end = True

    return buff


def do_in_buff(in_buff):
    global data_stack
    tokens = in_buff.split()

    if tokens[0] == ':':
        add_word_to_dict(tokens)
        return

    ds_original_state = data_stack
    for token in tokens:
        try:
            integer = int(token)
            data_stack.insert(0, integer)
        except ValueError:
            if do_word(token):
                pass
            else:
                print("Error: The word '{}' is not defined!".format(token))
                data_stack = ds_original_state
                return


# main
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("       	  MTKFORTH		     ")
print("                            	 ")
print(" - Hint: type 'words' (with 	 ")
print("   no qoutes) to list words 	 ")
print("								 ")
print(" - Click Home key to exit the ")
print("   program    	             ")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("")

try:
    while run:
    	in_buff = get_input()
        if not in_buff: continue  # note error if user does not enter anything at prompt then presses return - fix me
    	do_in_buff(in_buff)
except KeyboardInterrupt:
    pass  # ctr-c will exit, on numworks just click home key to exit
