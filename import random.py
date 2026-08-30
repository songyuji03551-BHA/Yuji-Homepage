import random
import time
from wordfreq import top_n_list

word_pool=top_n_list("en", 5000)
word_pool=[w for w in word_pool if len(w) >=3]

max_problems=100
target_correct=10

problem_count=0
correct_count=0
wrong_count=0

typed_chars=0
correct_chars=0

print("영어 타자 게임")
print("실제 영어 단어 자동 생성!")
print("10문제 맞추면 종료")
input("엔터 누르면 시작")

start_time=time.time

while problem_count<max_problems and correct_counts<target_correct:
    q=random.choice(word_pool)

    problem_count +=1

    print("\n---------------")
    print(f"문{problem_count}")
    print("단어:", q)

    user=input("입력:")

    typed_chars +=len(user)

    if user ==q:
        print("정답!!")
        correct_count +=1
        correct_chars += len(q)
    else:
        print("오답!!")
        print("정답:", q)

        wrong_count +=1

        same=0
        for a, b in zip(user, q):
            if a==b:
                same +=1
        correct_chars +=same

end_time=time.time()

elasped= end_time-start_time

if typed_chars>0:
    accuracy=(correct_chars/ typed_chars) *100
else:
    accuracy=0
