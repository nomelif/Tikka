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
    return {"Int":"int", "Str":"char*", "Unit":"void"}[typestring]

global closures
global addClosure
global finishClosureLine
global lastAnonFun
closures, addClosure, finishClosureLine = getReceiverArray()
lastAnonFun = 0

def parseAnonfun(ast, variables):
    global closures
    global addClosure
    global finishClosureLine
    global lastAnonFun
    lastAnonFun = lastAnonFun+1
    addClosure("void __AnonFun"+str(lastAnonFun)+"(){")
    compileBody(ast, addClosure, finishClosureLine, variables)
    addClosure("}")
    return "__AnonFun"+str(lastAnonFun)+"();"

def generate(ast):
    moduleName = ast["module"]
    emitCode("// Compiling module \""+moduleName+"\".")
    emitCode("""
#include <stdio.h>
#include <stdlib.h>

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
    for instruction in body:
        if instruction["type"] == "ternary":
            compileBody(instruction["condition"], emit, closeInstr, variables.copy())
            emit(" ? ", end="")
            return1 = compileBody(instruction["trueBranch"], emit, closeInstr, variables.copy())
            emit(" : ", end="")
            return2 = compileBody(instruction["falseBranch"], emit, closeInstr, variables.copy())
            hasOutput = return1["hasOutput"] or return2["hasOutput"]
            if return1["bodyType"] != return2["bodyType"]:
                raise ValueError("ternary condition branches should be of same type")
            bodyType = return1["bodyType"]
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
            emit("itoa(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Int":
                raise ValueError("itoa expects an integer but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            bodyType = "Str"
        elif instruction["type"] == "booltoa":
            emit("booltoa(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Bool":
                raise ValueError("booltoa expects a boolean but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            bodyType = "Str"
        elif instruction["type"] == "arrtostr":
            emit("arrtostr(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Arr":
                raise ValueError("booltoa expects an array but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            bodyType = "Str"
        elif instruction["type"] == "raw_input":
            emit("raw_input(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Str":
                raise ValueError("raw_input expects a string but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            bodyType = "Str"
        elif instruction["type"] == "strtoi":
            emit("atoi(", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            if returnData["bodyType"] != "Str":
                raise ValueError("strtoi expects a string but a value of type "+returnData["bodyType"]+" was given.")
            emit(")", end="")
            bodyType = "Int"
        elif instruction["type"] == "constant_str":
            emit("\""+instruction["value"]+"\"", end="")
            bodyType = "Str"
        elif instruction["type"] == "constant_int":
            emit(instruction["value"], end="")
            bodyType = "Int"
        elif instruction["type"] == "constant_bool":
            if instruction["value"] == "True":
                emit("1", end="")
            else:
                emit("0", end="")
            bodyType = "Bool"
        elif instruction["type"] == "assignment":
            if instruction["variable"] in variables.keys():
                emit(instruction["variable"]+" = ", end="")
            else:
                emit("auto "+instruction["variable"]+" = ", end="")
            returnData = compileBody(instruction["body"], emit, closeInstr, variables.copy())
            closeInstr()
            variables[instruction["variable"]] = returnData["bodyType"]
            bodyType = "Unit"
        elif instruction["type"] == "variable_read":
            emit(instruction["variable"], end="")
            bodyType = variables[instruction["variable"]]
        elif instruction["type"] == "sum":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" + ", end="")
                i = i + 1
            bodyType = "Int"
        elif instruction["type"] == "sub":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" - ", end="")
                i = i + 1
            bodyType = "Int"
        elif instruction["type"] == "mul":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" * ", end="")
                i = i + 1
            bodyType = "Int"
        elif instruction["type"] == "div":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" / ", end="")
                i = i + 1
            bodyType = "Int"
        elif instruction["type"] == "mod":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" % ", end="")
                i = i + 1
            bodyType = "Int"
        elif instruction["type"] == "eq":
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
            bodyType = "Bool"
        elif instruction["type"] == "gt":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" > ", end="")
                i = i + 1
            bodyType = "Bool"
        elif instruction["type"] == "neq":
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i + 1 < len(instruction["values"]):
                    emit(" != ", end="")
                i = i + 1
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
                result = compileBody(line, emit, closeInstr, variables)
                hasOutput = result["hasOutput"]
                bodyType = result["bodyType"]
        elif instruction["type"] == "constant_array":
            emit("{", end="")
            i = 0
            while i < len(instruction["values"]):
                compileBody(instruction["values"][i], emit, closeInstr, variables.copy())
                if i != len(instruction["values"]) - 1:
                    emit(", ", end="")
                i = i + 1
            emit("}", end="")
            hasOutput = False
            bodyType = "Arr"
    #print(hasOutput)
    return {"hasOutput":hasOutput, "bodyType":bodyType}

def addSemicolon():
    print(";")
