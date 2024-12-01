# Project_Financial
The topic of this projects is financial. It's about financial indicators scrapping.  

# 1. 개요

## 1-1. 설명
\- 미국 주식 종목 선정시 참고할 수 있는 기본 지표들을 스크래핑 하는 코드를 작성한다.  
\- 1차 목표는 수동으로 실행시키는 코드의 완성, 2차 목표는 클라우드를 활용해 배치 프로세스로 일정 주기마다 자동으로 종목의 지표들을 받아올 수 있도록 한다.

# 2. 코드

## 2-1. 전체적인 흐름

\- (1) NYSE에서 나스닥에 상장된 전 종목 리스트 스크랩 -> (2) 각 종목에 대해 야후 파이낸스에서 PER, PBR 등 투자 기본 지표들 받아오기 -> (3) 각 지표들에 기준을 두고 저PER, 저PBR 종목 등 선별하기  
\- 각 단계에서 사용된 주요 패키지, 라이브러리는 다음과 같다.  
(1) : selenium  
(2) : yfinance  
(3) : pandas, openpyxl  

## 2-2. nasdaq_stocks_indicators_CMC.py

\- https://companiesmarketcap.com/ 에서 미국 기업 목록을 csv파일로 다운로드 받는 경우  

## 2-2. nasdaq_stocks_indicators_NYSE.py

\- selenium으로 NYSE에서 미국 기업 목록을 직접 긁어서 엑셀 파일로 만드는 경우  

# 3. 피드백

## 3-1. 추가, 수정할 것들

### 1. 241103_NYSE에서 나스닥 상장 전 종목 받아오기
\- 지금은 다음 종목들이 있는 페이지로 넘길 때 WebDriverWait(driver, 3) 이렇게 일정 시간 대기하라고 하고 있다. 하지만 [이 블로그](https://june98.tistory.com/11)에서는 일정 시간을 정한 게 아닌, 해당 요소가 화면에 표시될 때까지 대기하는 것도 가능하다.  
\-> 지금 다시 보니까 이미 내가 작성한 코드가 해당 기능을 적용한 것.
### 2. 241104_OOP 스타일로 코드 리팩토링
\- 지금은 변수, 함수들 너무 난잡하고 한 눈에 안 들어옴  
\-> 일단 OOP 스타일로 다시 정리하긴 했는데, 엄청 깔끔한 느낌은 들지 않는다. 매우 소소하게 깔끔해진 느낌? 무엇보다 챗gpt한테도 OOP 스타일로 리팩토링 해달라고 했는데 나보다 더 잘한 것 같음.  
\-> 310줄 -> 290줄로 줄이긴 함.
### 3. 241104_엑셀 생성하고 수정하는 함수의 사용 빈도, 존재 이유 생각
\- 속도에 방해되는 것 아닌가? 안정성도 떨어지는 것 같고. 그냥 데이터프레임 만들어서 파이썬 내부에서 여차저차 수정하는 게 낫지 않나? 데이터프레임 만들고 concat을 하는 게 낫지 않은가

## 3-2. 공부할 것들  

### 1. 멀티쓰레딩, 멀티프로세싱 차이
\- 나는 멀티쓰레딩 사용했는데, 멀티프로세싱과 뭐가 다른지? 각각 언제 사용해야 하는지? 스레드와 프로세스는 뭔지?
### 2. 챗gpt OOP vs 내 OOP
\- 챗gpt가 나보다 코드 줄 수를 훨씬 많이 줄였음. 비교해보자.  
### 3. stderr, redirect? 이것들 다 뭔지  
\- client404 에러는 except로 예외처리 해도 자꾸 뜨던데, 이걸 없앨 수 있는 방법이 있다.

## 3-3. 배운 것들
### 1. 프로세스 vs 스레드
\- 웹 스크랩 같은 IO 작업 많은 애들은 멀티쓰레딩이 낫다.  
### 2. 에러들 정리
\- 특정 패키지의 내부 클래스의 함수들에서 문제가 발생한 경우에도, 잘 살펴보면 원인 발견, 해결 가능  
\- 예외처리 하는 방법. Exception하면 여러 개 예외처리 가능  
\- 에러 문구도 안 뜨게 가능 : stderr 관련  
```
import yfinance as yf
import contextlib
import io

def check_symbol(symbol):
    stock = yf.Ticker(symbol)
    try:
        # 에러 메시지를 무시하기 위해 stderr를 일시적으로 redirect
        with contextlib.redirect_stderr(io.StringIO()):
            info = stock.info
        # info가 비어있으면 유효하지 않은 심볼로 간주
        if info and 'symbol' in info:
            return True  # 유효한 symbol
    except Exception:
        pass  # 에러가 발생해도 아무것도 출력되지 않음
    return False  # 유효하지 않은 symbol

# 테스트
symbols = ["AAPL", "INVALIDSYM", "MSFT"]
for symbol in symbols:
    if check_symbol(symbol):
        print(f"{symbol} is valid.")
    else:
        print(f"{symbol} is invalid.")

```

### 3. 판다스 관련
\- to_excel()시 index=True, index_label="No" : 이거 안 해주면 Unnamed 컬럼 생기면서 새로 적재하기 힘들어짐  

### 4. OOP 연습 필요

# 4. 에러 목록

## 4-1. 순번 / 에러명 / 원인 / 해결  

\- 1. / client 404에러 / yfinance stock.info 조회 시 안 뜨는 티커들 존재 / stock.info 전에 try except 예외처리. 사실, 그냥 add_stock_info 함수 내에서 반복문 시작하자마자 예외처리 조졌으면 다 잘 해결됐을 거임  
\- 2. / json.decoder.JSONDecodeError / 1번과 같음 / 1번과 같음  
\- 3. / AttributeError: 'float' object has no attribute 'upper' / stock_data = yf.Ticker(symbol) 부분에서 뜨는 오류. Symbol중에서 float인 게 하나도 없는데 왜 뜨는지는 모르겠음 / stock_data = yf.Ticker(symbol) 전에 try except 예외처리  
\- 4. / Thread Exception / 2번이나 다른 이유로 쓰레드 작업 비정상 종료 시 발생 / 예외처리 적절하게 해줘서 1, 2 등 오류 안 뜨면 해결  
\- 5. / ValueError: No objects to concatenate / Thread들이 비정상 종료되어 합칠 데이터프레임들이 하나도 없어서 발생 / 1개 쓰레드라도 작업 완료하면 안 뜸. 3을 해결하면 되고, 이를 위해 1, 2번 해결 필요  
\- 6. / 완성된 엑셀에 일부 종목들 누락 / Thread간 속도 차이? 일부 쓰레드 작업 완료 안 됐는데 프로그램 종료 / 불완전 해결. 1~4번 에러들을 해결하려다보니 241119 성공. 아마 1번 에러가 지대한 영향을 끼친 게 아닐까? try except 예외처리 위치로 해결했다고 봐야할듯  
