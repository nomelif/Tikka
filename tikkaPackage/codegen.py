def emitCode(code, **kwargs):
    print(code, **kwargs)

def getReceiverArray():
    arr = []
    def add(val, **kwargs):
        if "end" in kwargs.keys():
            arr.append(val + kwargs["end"])
        else:
            arr.append(val+"\n")
    def finishLine():
        add(";")
    return (arr, add, finishLine)

def toCType(typestring):
    return {"Int":"int", "Str":"char*", "Unit":"void", "Bool":"char"}[typestring]

global closures
global addClosure
global finishClosureLine
global lastAnonFun
global knownFns
knownFns = {}
closures, addClosure, finishClosureLine = getReceiverArray()
lastAnonFun = 0

def parseAnonfun(ast, variables):
    global closures
    global addClosure
    global finishClosureLine
    global lastAnonFun
    lastAnonFun = lastAnonFun+1
    addClosure("void __AnonFun"+str(lastAnonFun)+"(){")
    compileBody(ast, addClosure, finishClosureLine, variable)
    addClosure("}")
    return "__AnonFun"+str(lastAnonFun)+"();"

def parseFun(ast, variables, name):
    global closures
    global addClosure
    global finishClosureLine
    global lastAnonFun
    global knownFns
    rubish, addToRubish, endRubish = getReceiverArray()
    arguments = {}
    for arg in variables:
        arguments[arg[0]] = arg[1]
    result = compileBody(ast, addToRubish, endRubish, arguments.copy(), True)
    knownFns[name] = result["bodyType"]
    addClosure(toCType(result["bodyType"]) + " " + name + "(" + ", ".join(list([toCType(arg[1]) + " " + arg[0] for arg in variables])) + "){")
    compileBody(ast, addClosure, finishClosureLine, arguments.copy(), True)
    addClosure("}")
    return "__AnonFun"+str(lastAnonFun)+"();"

def generate(ast):
    moduleName = ast["module"]
    emitCode("// Compiling module \""+moduleName+"\".")
    emitCode("""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>

// Standard squareroot

int intSqrt(int toSqrt){
    return (int) sqrt((double) toSqrt);
}

// Standard boolean-to-string method

char* booltoa(int i){
    if(i)
        return "True";
    else
        return "False";
}

// Standard int-to-string method

char* itoa(int i){
    char* b = malloc(22); // Awful! Kill with fire!!!!
    char const digit[] = "0123456789";
    char* p = b;
    if(i<0){
        *p++ = '-';
        i *= -1;
    }
    int shifter = i;
    do{
        ++p;
        shifter = shifter/10;
    }while(shifter);
    *p = '\0';
    do{
        *--p = digit[i%10];
        i = i/10;
    }while(i);
    return b;
}

// Standard slice function

char* slice(char* a_str, int start, int end)
{
    char *to = (char*) malloc(end-start+1);
    strncpy(to, a_str+start, end-start);
    return to;
}


char* raw_input(char* prompt){
char* stringbuf = malloc(100);

printf("%s", prompt);
fgets(stringbuf, 100, stdin);
stringbuf[strlen(stringbuf)-1] = '\0';
return stringbuf;
}
""")

    if "functions" in ast.keys():
        for function in ast["functions"]:
            arr, add, finishLine = getReceiverArray()
            result = compileBody(function["body"], add, finishLine, {})
            emitCode(toCType(result["bodyType"]) + " ", end="")
            emitCode(function["header"]+"{")
            if result["bodyType"] != "Unit":
                compileBody(function["body"], emitCode, addSemicolon, {}, True)
            else:
                emitCode("".join(arr))
            emitCode("}\n")
    arr, add, finishLine = getReceiverArray()
    add("int main(){")
    compileBody(ast["body"], add, finishLine, {})
    add("}")
    global closures
    for closure in closures:
        emitCode(closure, end="")
    emitCode("")
    for line in arr:
        emitCode(line, end="")
    emitCode("")


def compileBody(body, emit, closeInstr, variables, addReturn = False):
    hasOutput = False
    bodyType = "Unit"
    instrIndex = 0
    for instruction in body:
        if instruction["type"] == "ternary":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            compileBody(instruction["condition"], emit, closeInstr, variables.copy())
            emit(" ? ", end="")
            return1 = compileBody(instruction["trueBranch"], emit, closeInstr, variables.copy())
            emit(" : ", end="")
            return2 = compileBody(instruction["falseBranch"], emit, closeInstr, variables.copy())
            hasOutput = return1["hasOutput"] or return2["hasOutput"]
            if return1["bodyType"] != return2["bodyType"]:
                raise ValueError("ternary condition branches should be of same type")
            bodyType = return1["bodyType"]
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
        elif instruction["type"] == "print":
            hasOutput = True
            emit("printf(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Str":
                raise ValueError("print expects a string but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            closeInstr()
            bodyType = "Unit"
        elif instruction["type"] == "itoa":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("itoa(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Int":
                raise ValueError("itoa expects an integer but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "booltoa":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("booltoa(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Bool":
                raise ValueError("booltoa expects a boolean but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "arrtostr":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("arrtostr(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Arr":
                raise ValueError("booltoa expects an array but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "raw_input":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("raw_input(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Str":
                raise ValueError("raw_input expects a string but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "strtoi":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("atoi(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Str":
                raise ValueError("strtoi expects a string but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "fnCall":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit(instruction["name"]+"(", end="")
            i = 0
            for arg in instruction["body"]:
                compileBody([arg], emit, closeInstr, variables.copy())
                if i < len(instruction["body"])-1:
                    emit(", ", end="")
                i = i + 1
            #returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            global knownFns
            bodyType = knownFns[instruction["name"]]
        elif instruction["type"] == "sqrt":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("intSqrt(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Int":
                raise ValueError("sqrt expects an integer but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "get":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            arrData = compileBody(instruction["arguments"][0], emit, closeInstr, variables.copy())
            emit("[", end="")
            returnData = compileBody(instruction["arguments"][1], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Int":
                raise ValueError("'get' expects an integer as the index but a value of type "+returnData["bodyType"]+" was given.")
            if arrData["bodyType"][0] != "Arr":
                raise ValueError("'get' expects an array for the body but a value of type "+returnData["bodyType"]+" was given.")
            emit("]", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = arrData["bodyType"][1]
        elif instruction["type"] == "slice":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("slice(", end="")
            arrData = compileBody(instruction["arguments"][0], emit, closeInstr, variables.copy())
            emit(", ", end="")
            returnData = compileBody(instruction["arguments"][1], emit, closeInstr, variables.copy())
            emit(", ", end="")
            returnData2 = compileBody(instruction["arguments"][2], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Int":
                raise ValueError("'slice' expects an integer as the delimiter but a value of type "+returnData["bodyType"]+" was given.")
            if returnData2["bodyType"] != "Int":
                raise ValueError("'slice' expects an integer as the delimiter but a value of type "+returnData["bodyType"]+" was given.")
            if arrData["bodyType"] != "Str":
                raise ValueError("'slicec' expects a string for the body but a value of type "+arrData["bodyType"]+" was given.")
            emit(")", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "constant_str":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("\""+instruction["value"]+"\"", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Str"
        elif instruction["type"] == "constant_int":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit(instruction["value"], end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "constant_bool":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            if instruction["value"] == "True":
                emit("1", end="")
            else:
                emit("0", end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Bool"
        elif instruction["type"] == "assignment":
            if instruction["variable"] in variables.keys():
                emit(instruction["variable"]+" = ", end="")
            else:
                arr, add, addS = getReceiverArray()
                returnData = compileBody(instruction["body"], add, addS, variables.copy())
                if returnData["bodyType"][0] == "Arr":
                    emit("auto *"+instruction["variable"]+"[] = ", end="")
                else:
                    emit("auto "+instruction["variable"]+" = ", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            closeInstr()
            variables[instruction["variable"]] = returnData["bodyType"]
            bodyType = "Unit"
        elif instruction["type"] == "variable_read":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit(instruction["variable"], end="")
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = variables[instruction["variable"]]
        elif instruction["type"] == "sum":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" + ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "sub":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" - ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "mul":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" * ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "div":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" / ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "mod":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" % ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Int"
        elif instruction["type"] == "eq":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            if len(instruction["values"]) == 2:
                arr, add, finishLine = getReceiverArray()
                returnValue1 = compileBody(instruction["values"][0], add, finishLine, variables.copy())
                returnValue2 = compileBody(instruction["values"][1], add, finishLine, variables.copy())
                if returnValue1["bodyType"] == "Str" and returnValue2["bodyType"] == "Str":
                    emit("strcmp(", end="")
                    emit(arr[0], end="")
                    emit(", ", end="")
                    emit(arr[1], end="")
                    emit(") == 0", end="")
                    bodyType = "Bool"
                    continue
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" == ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Bool"
        elif instruction["type"] == "gt":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" > ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Bool"
        elif instruction["type"] == "neq":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" != ", end="")
                i = i + 1
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
            bodyType = "Bool"
        elif instruction["type"] == "if":
            emit("if(", end="")
            conditionType = compileBody(instruction["condition"], emit, closeInstr, variables.copy())["bodyType"]
            if not conditionType == "Bool":
                raise ValueError("if-clause requires a boolean value for the condition. Got a "+conditionType+".")
            emit("){")
            compileBody(instruction["body"], emit, closeInstr, variables.copy())
            emit("}")
        elif instruction["type"] == "while":
            emit("while(", end="")
            conditionType = compileBody(instruction["condition"], emit, closeInstr, variables.copy())["bodyType"]
            if not conditionType == "Bool":
                raise ValueError("while-clause requires a boolean value for the condition. Got a "+conditionType+".")
            emit("){")
            compileBody(instruction["body"], emit, closeInstr, variables.copy())
            emit("}")
        elif instruction["type"] == "body":
            for line in instruction["body"]:
                result = compileBody(line, emit, closeInstr, variables, instrIndex == len(body)-1 and addReturn)
                hasOutput = result["hasOutput"]
                bodyType = result["bodyType"]
        elif instruction["type"] == "function_declaration":
            parseFun(instruction["body"], instruction["arguments"], instruction["name"])
        elif instruction["type"] == "constant_array":
            if instrIndex == len(body)-1 and addReturn:
                emit("return ", end="")
            emit("{", end="")
            i = 0
            returnData = ""
            while i < len(instruction["values"]):
                returnData = compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i != len(instruction["values"]) - 1:
                    emit(", ", end="")
                i = i + 1
            emit("}", end="")
            hasOutput = False
            bodyType = ["Arr", returnData["bodyType"]]
            if instrIndex == len(body)-1 and addReturn:
                emit(";")
        instrIndex = instrIndex + 1
    #print(hasOutput)
    return {"hasOutput":hasOutput, "bodyType":bodyType}

def addSemicolon():
    print(";")
