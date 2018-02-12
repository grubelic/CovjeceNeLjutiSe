INFINITE = 1000000
INDEX = 100
DEPLOY = 25
HOME_DEPTH = 150
PROGRESS = 1
DEFENSIVE = 1
OFFENSIVE = 1
DISTANCE = 1
FIRST_COLOR = 0
def convertPosition(position, color, relativeTo): #iz sustava color u relativeTo
    return (position - 1 + (color - relativeTo + 4)*10)%40+1
def dist(c1, p1, c2, p2):
    if(p1 <= 0 or p2 <= 0):
        return INFINITE
    distance = convertPosition(p2, FIRST_COLOR, c1) - convertPosition(p1, FIRST_COLOR, c1)
    if(distance > 40 - convertPosition(p2, FIRST_COLOR, c2)):
        return INFINITE
    #print(p2, p1, distance)
    return distance
def value(p, d, c, index):
    v = index * INDEX
    op = p[c][index]
    if(op == 0 and d == 6):
        np = 1
        v += DEPLOY
    elif(op < 0):
        np = op - d
        v += -np * HOME_DEPTH
    else:
        temp = (op - 1 + d) % 40
        np = (temp + 1) - (temp + 1) * (temp // 39)
        v += (np < 0) * -np * HOME_DEPTH + (np > 0) * PROGRESS * np
    for i in range(4):
        if (i != c):
            for j in range(4):
                distance = dist(c, np, i, p[i][j])
                if(distance != INFINITE):
                    v += (40 - distance)**2 * (-DEFENSIVE + (distance >= 0) * (DEFENSIVE + OFFENSIVE)) * DISTANCE
    return v
def movable(p, c, index, k):
    if(p[c][index] == 0 and k == 6):
        for i in range(4):
            if(convertPosition(p[c][i], FIRST_COLOR, c) == 1):
               return False
        return True
    if(p[c][index] == 0):
        return False
    if(p[c][index] < 0):
        if(p[c][index] - 3 + index - k >= -4):
            for i in range(4):
                if(p[c][index] - k == p[c][i]):
                    return False
            return True
        return False
    px = convertPosition(p[c][index], FIRST_COLOR, c)
    if(px + k > 40):
        if(px + k + (3 - index) > 44):
            return False
        pn = 40 - px - k
    else:
        pn = convertPosition(px + k, c, FIRST_COLOR)
    if(pn in p[c]):
        return False
    return True
def main(positions, dice, color, output):
    for i in range(4):
        if movable(positions, color, i, dice) and not("MIOC"[i] in output):
            print(positions, dice, color, output, sep = "\n")
    #print()
    maxV = -INFINITE
    maxI = output[-1]
    for i in output:
        j = "MIOC".index(i)
        temp = value(positions, dice, color, j) - value(positions, 0, color, j)
        #print(color, i, temp)
        if(temp >= maxV):
            maxI = i
            maxV = temp
    return maxI
if (__name__ == "__main__"):
    for i in range(-4, 41):
        print()
        print(i, main([[0,0,7,0], [0,0,i,0], [0,0,0,0], [0,0,0,0]], 6, 0, "MIOC"))
    input()
