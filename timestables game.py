import random

score=0

for i in range(10):
    a=random.randint(2,12)
    b=random.randint(1,12)

    answer= int (input(f"{a} x {b} = "))

    if answer == a*b:
        print("정답!")
        score=score+1
    else:
        print("틀림!")
    
print("맞춘 개수:", score)