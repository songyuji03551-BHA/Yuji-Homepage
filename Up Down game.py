import random
answer=random.randint(1,50)

for i in range(5):
    guess=int(input("숫자 입력(1~50):"))

    if guess>answer:
        print("DOWN")
    elif guess<answer:
        print("UP")
    else:
        print("정답!")
        break

print("게임 끝! 정답:", answer)