import json

def read(fname):
    with open(fname, "r") as file:
        return json.load(file)

def pretreat(text):
    parenBalance = 0
    insideString = False
    result = ""
    for line in text.split("\n"):
        prevChar = ""
        if insideString:
            result = result + "\\n" + line
        elif parenBalance == 0:
            result = result + "\n" + line
        else:
            result = result + line + ";"
        for char in line:
            if char == "\"" and prevChar != "\\":
                insideString = not insideString
            elif char == "(" and not insideString:
                parenBalance = parenBalance + 1
            elif char == ")" and not insideString:
                parenBalance = parenBalance - 1
            prevChar = char

    #if insideString:
    #    raise ValueError("Unmatched quotes.")
    #elif parenBalance != 0:
    #    raise ValueError("Unmatched parantheses.")
    return result

def parse(fname):
    text = ""
    resultTree = []
    with open(fname, "r") as file:
        for line in file:
            text = text + line
    text = pretreat(text)
    for line in text.split("\n"):
        exp = parseLine(line)
        if exp != None:
            resultTree.append(exp)
    #print(resultTree)
    return {"module":fname, "body":resultTree}

def parseLine(line):
    line = line.strip(";")
    if ";" in line:
        insideString = False
        parenDepth = 0
        prevChar = ""
        result = [""]
        for character in line:
            if character == "\"" and not prevChar == "\\":
                insideString = not insideString
            elif character == "(" and not insideString:
                parenDepth = parenDepth + 1
            elif character == ")" and not insideString:
                parenDepth = parenDepth - 1

            if not insideString and parenDepth == 0 and character == ";":
                result.append("")
            else:
                result[-1] = result[-1] + character
        finalLines = []
        for splitLine in result:
            if not splitLine == "":
                finalLines.append(splitLine)
        if len(finalLines) != 1:
            result = {"type":"body", "body":[]}
            for finalLine in finalLines:
                result["body"].append([parseLine(finalLine.strip())])
            return result
    if line.strip() == "":
        return None
    if line.strip()[0] == "(" and line.strip()[-1] == ")" and "," in line:
        i = 0
        insideString = False
        parenDepth = 0
        prevChar = ""
        commas = []
        while i < len(line.strip()):
            if line.strip()[i] == "\"" and prevChar != "\\":
                insideString = not insideString
            elif line.strip()[i] == "(" and not insideString:
                parenDepth = parenDepth + 1
            elif line.strip()[i] == ")" and not insideString:
                parenDepth = parenDepth - 1
            elif line.strip()[i] == "," and not insideString and parenDepth == 1:
                commas.append(i)
            if parenDepth == 0:
                i = i + 1
                break
            prevChar = line.strip()[i]
            i = i + 1
        if parenDepth == 0 and i == len(line.strip()):
            body = line.strip()[1:-1]
            elements = []
            prevSplit = 0
            for index in commas:
                elements.append(body.strip()[prevSplit:index].strip(",").strip())
                prevSplit = index
            elements.append(body.strip()[prevSplit:].strip(",").strip())
            result = []
            for element in elements:
                result.append([parseLine(element)])
            return {"type":"constant_array", "values":result}
    if line.strip() == "True":
        return {"type":"constant_bool", "value":"True"}
    if line.strip() == "False":
        return {"type":"constant_bool", "value":"False"}
    elif line.strip().startswith("print("):
        return {"type":"print", "body":[parseLine(line.strip()[6:-1])]}
    elif line.strip()[0] == "\"" and line.strip()[-1] == "\"":
        prevC = ""
        isStr = True
        for character in line.strip()[1:-1]:
            if (not prevC == "\\") and character == "\"":
                isStr = False
            prevC = character
        if isStr:
            return {"type":"constant_str", "value":line.strip()[1:-1]}
    if line.strip().isdigit() or (line.strip()[0] == "-" and line[1:].isdigit()):
        return {"type":"constant_int", "value":line.strip()}
    if "=" in line and isName(line.split("=")[0].strip()):
        if not ("==" in line and line.index("=") == line.index("==")):
            return {"type":"assignment", "variable":line.split("=")[0].strip(), "body":[parseLine("=".join(line.split("=")[1:]).strip())]}
    if isName(line.strip()):
        return {"type":"variable_read", "variable":line.strip()}

    if "?" in line and ":" in line:
        conditionEnd = 0
        conditionFound = False
        insideString = False
        parenDepth = 0
        prevChar = ""
        while conditionEnd < len(line) and not conditionFound:
            if line[conditionEnd] == "\"" and prevChar != "\\":
                insideString = not insideString
            elif line[conditionEnd] == "(" and not insideString:
                parenDepth = parenDepth + 1
            elif line[conditionEnd] == ")" and not insideString:
                parenDepth = parenDepth - 1
            elif line[conditionEnd] == "?" and parenDepth == 0 and not insideString:
                conditionFound = True
                break
            prevChar = line[conditionEnd]
            conditionEnd = conditionEnd + 1
        splitPoint = conditionEnd
        splitFound = False
        while splitPoint < len(line) and not splitFound:
            if line[splitPoint] == "\"" and prevChar != "\\":
                insideString = not insideString
            elif line[splitPoint] == "(" and not insideString:
                parenDepth = parenDepth + 1
            elif line[splitPoint] == ")" and not insideString:
                parenDepth = parenDepth - 1
            elif line[splitPoint] == ":" and parenDepth == 0 and not insideString:
                splitFound = True
                break
            prevChar = line[splitPoint]
            splitPoint = splitPoint + 1
        if conditionFound and splitFound:
            return {"type":"ternary", "condition":[parseLine(line[:conditionEnd].strip())], "trueBranch":[parseLine(line[conditionEnd+1:splitPoint])], "falseBranch":[parseLine(line[splitPoint+1:])]}
    if "==" in line:
        signIndices = parseSign(line, "==", "eq")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "==", "eq", signIndices)
    if ">" in line:
        signIndices = parseSign(line, ">", "gt")
        if not len(signIndices) == 0:
            return parseSignToTree(line, ">", "gt", signIndices)
    if "!=" in line:
        signIndices = parseSign(line, "!=", "neq")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "!=", "neq", signIndices)
    if "+" in line:
        signIndices = parseSign(line, "+", "sum")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "+", "sum", signIndices)
    if "-" in line:
        signIndices = parseSign(line, "-", "sub")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "-", "sub", signIndices)
    if "*" in line:
        signIndices = parseSign(line, "*", "mul")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "*", "mul", signIndices)
    if "/" in line:
        signIndices = parseSign(line, "/", "div")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "/", "div", signIndices)
    if "%" in line:
        signIndices = parseSign(line, "%", "mod")
        if not len(signIndices) == 0:
            return parseSignToTree(line, "%", "mod", signIndices)

    if "(" in line and isName(line.split("(")[0].strip()):
        i = firstIndex = len(line.split("(")[0])
        parenDepth = 0
        insideString = False
        prevChar = ""
        while i < len(line):
            if line[i] == "(" and not insideString:
                parenDepth = parenDepth + 1
            elif line[i] == ")" and not insideString:
                parenDepth = parenDepth - 1
            elif line[i] == "\"" and prevChar != "\\":
                insideString = not insideString
            if parenDepth == 0:
                i = i + 1
                break
            i = i + 1
        if line[i:].strip() == "":
            if line.split("(")[0].strip() == "itoa":
                return {"type":"itoa", "body":[parseLine(line[firstIndex+1:i-1].strip())]}
            if line.split("(")[0].strip() == "booltoa":
                return {"type":"booltoa", "body":[parseLine(line[firstIndex+1:i-1].strip())]}
            if line.split("(")[0].strip() == "strtoi":
                return {"type":"strtoi", "body":[parseLine(line[firstIndex+1:i-1].strip())]}
            if line.split("(")[0].strip() == "raw_input":
                return {"type":"raw_input", "body":[parseLine(line[firstIndex+1:i-1].strip())]}
            if line.split("(")[0].strip() == "arrtostr":
                return {"type":"arrtostr", "body":[parseLine(line[firstIndex+1:i-1].strip())]}
            raise ValueError("Unrecognized method "+line.split("(")[0].strip()+".")

        else:
            if line[i:].strip()[0] == "(" and line[i:].strip()[-1] == ")":
                condition = line[firstIndex+1:i-1].strip()
                body = line[i:].strip()
                i = 0
                parenDepth = 0
                insideString = 0
                prevChar = ""
                while i < len(body):
                    if body[i] == "\"" and prevChar != "\\":
                        insideString = not insideString
                    elif body[i] == "(" and not insideString:
                        parenDepth = parenDepth + 1
                    elif body[i] == ")" and not insideString:
                        parenDepth = parenDepth - 1
                    if parenDepth == 0:
                        break
                    prevChar = body[i]
                    i = i + 1
                if i == len(body) - 1 and parenDepth == 0:
                    if line.split("(")[0].strip() == "if":
                        return {"type":"if", "condition":[parseLine(condition)], "body":[parseLine(body[1:-1].strip())]}
                    if line.split("(")[0].strip() == "while":
                        return {"type":"while", "condition":[parseLine(condition)], "body":[parseLine(body[1:-1].strip())]}

    return None

def isName(pattern):
    if len(pattern) == 0:
        return False
    if pattern[0].isalpha():
        for letter in pattern[1:]:
            if not (letter.isalnum() or letter == "_"):
                return False
        return True
    else:
        return False

def parseSign(line, sign, operation):
    signIndices = []
    prevChar = ""
    insideString = False
    parenDepth = 0
    i = 0
    while i < len(line):
        character = line[i]
        if line[i:i+len(sign)] == sign and not insideString and parenDepth == 0:
            signIndices.append(i)
        elif character == "\"" and not prevChar == "\\":
            insideString = not insideString
        elif character == "(" and not insideString:
            parenDepth = parenDepth + 1
        elif character == ")" and not insideString:
            parenDepth = parenDepth - 1
        prevChar = character
        i = i + 1
    return signIndices

def parseSignToTree(line, sign, operation, signIndices):
    signIndices.append(len(line))
    prevIndex = 0
    countableParts = []
    for index in signIndices:
        if prevIndex == 0:
            countableParts.append([parseLine(line[0:index].strip())])
        else:
            countableParts.append([parseLine(line[prevIndex+len(sign)-1:index].strip())])
        prevIndex = index + 1
    return {"type":operation, "values":countableParts}
