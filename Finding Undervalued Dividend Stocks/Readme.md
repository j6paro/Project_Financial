# 1. 개요

## 1-1. 설명
\- 배당귀족주들의 배당금과 배당률 이력을 확인해 저평가된 종목을 발굴한다.  

# 2. 코드

## 2-1. 전체적인 흐름

\- (1) 배당귀족주 리스트 수집 -> (2) 각 종목들에 대해 배당률, 배당금 계산 -> (3) 결과 저장 및 시각화  
\- 각 단계에서 사용된 주요 패키지, 라이브러리 또는 참고한 웹사이트는 다음과 같다.  
(1) : [배당귀족주 리스트 안내 블로그](https://blog.naver.com/polarisians/223609374301)  
(2) : yfinance, pandas  
(3) : pandas  

## 2-2. Finding Dividend Stocks.ipynb

\- 해당 코드를 부분별로 나눔  

### 2-2-1. 라이브러리 import  
```
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
```
\- yfinance : 야후 파이낸스에서 주식 기본 지표들을 스크래핑하기 위해 import 한다. 그런데 너무 많이 스크래핑 요청을 보내다 보면 야후 파이낸스에서 이를 봇으로 감지하는지 종종 알 수 없는 이유로 스크래핑이 중간에 멈추기도 한다.  
\- pandas : yfinance에서 수집한 배당금, 종가 데이터를 가공해 데이터프레임을 만들고 이를 저장한다.  
\- matplotlib.pyplot : 시각화에 사용  

### 2-2-2. 시각화 함수
```
# 시각화
def plot_data(df, ticker):
    # 한글 폰트 설정
    plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows의 맑은 고딕
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 그래프1
    ax1.set_xlabel('년도') # 수정. x축 label
    ax1.set_ylabel('배당률', color='red') # 수정. 그래프1 y축 label
    line1, = ax1.plot(df.index, df["Dividends yield rate"], 'ro--', markersize=4, label='배당률', color='red') # 그래프1 그리기
    ax1.tick_params(axis='y', labelcolor='red') # 그래프1 y축 색상 지정

    # 그래프1 숫자표시 : x축, y축 좌표에 값을 텍스트로 표시
    for i, v in enumerate(df.index): # x축 리스트에서 (인덱스, x축 리스트[인덱스]에 해당하는 value)를 가져온다.
        plt.text(v, df["Dividends yield rate"][i], round(df["Dividends yield rate"][i], 2), # x축 리스트[인덱스] : x축 좌표, y축 리스트[인덱스] : y축 좌표, y축 리스트[인덱스] : 표시할 숫자
                fontsize=9, # 텍스트 크기
                color='red', # 텍스트 색깔
                horizontalalignment='center', # 수평 위치 (left, center, right)
                verticalalignment='bottom', # 수직 위치 (top, center, bottom)
                # rotation=70 # 텍스트 각도
                )

    plt.xticks(rotation=45, fontsize=8) # 그래프 2 그리기 이전에 해야 x축 45도 돌아감
    
    # 그래프2
    ax2 = ax1.twinx()  # 두 번째 y축 생성
    ax2.set_ylabel('배당금', color='blue') # 수정. 그래프2 y축 label
    line2 = ax2.bar(df.index, df['Dividends'], label=ticker+"_배당금", color='blue') # 그래프2 그리기
    ax2.tick_params(axis='y', labelcolor='blue') # 그래프2 y축 색상 지정

    # 그래프2 숫자표시
    for i, v in enumerate(df.index):
        plt.text(v, df["Dividends"][i], round(df["Dividends"][i], 2),
                fontsize=9,
                color='blue',
                horizontalalignment='center',
                verticalalignment='bottom',
                # rotation=45
                )

    # 제목 및 범례 추가
    lines_labels = line1.get_label(), line2.get_label()
    handles= [line1, line2]
    plt.legend(handles, lines_labels, loc='upper left', fontsize=10, frameon=True)
    ax1.set_zorder(ax2.get_zorder() + 10) # 그래프1 zorder를 그래프2 zorder보다 무조건 높게. zorder 낮을수록 먼저 그려짐
    ax1.patch.set_visible(False) # 그래프1 레이어 투명하게
    plt.title(f'배당률 & 배당금 : {ticker}') # 수정. 그래프 제목
    fig.tight_layout()  # 레이아웃 조정
    
    plt.show()
```

### 2-2-3. yfinance로 배당률, 배당금 수집하여 데이터프레임 생성
```
DIR_SAVEFILE = "C:/coding/DA/dividends_info.xlsx" # 수정 필요. 테스트 데이터프레임들 저장할 엑셀 경로
DIR_DIVIDEND_ARISTOCRAT = "C:/Users/LG/Desktop/바탕화면/재테크/주식/배당귀족주 리스트.xlsx"
df_result_list = list() # df_merge 저장하기 위해 리스트 만들기
df_dividend_aristocrats = pd.read_excel(DIR_DIVIDEND_ARISTOCRAT) # 수정 필요. 배당귀족주 목록 데이터프레임으로 불러오기
lst_dividend_aristocrats = df_dividend_aristocrats["Ticker"]

# 배당률, 배당금, 종가 받아오는 함수
def scraping_stock_data(stock_ticker):
    ticker = stock_ticker # 특정 종목 티커
    stock = yf.Ticker(ticker) # 주식 데이터 다운로드
    dividends = stock.dividends # 역대 배당금 조회

    # 종가 데이터프레임 만들기
    df = yf.download(ticker) # 특정 종목 정보 받아오기
    df = df.reset_index() # 인덱스 초기화
    df["Year"] = df["Date"].astype('str').str.split('-').str[0] # 연도 컬럼 생성

    # 종가 피벗 테이블 만들기
    df_pivot_price = pd.pivot_table(df, values="Close", index="Year", aggfunc='mean') # 같은 년도의 종가 평균가
    df_pivot_price = df_pivot_price.rename(columns={ticker:str(ticker+"_closed")}) # 종가 피벗 테이블 컬럼명 바꾸기

    # 배당금 데이터프레임 만들기
    df_dividends = pd.DataFrame(dividends) # 배당금 시리즈 -> 배당금 데이터프레임
    df_dividends = df_dividends.reset_index() # 인덱스 초기화 -> 날짜 컬럼(Date) 생성
    df_dividends["Year"] = df_dividends["Date"].astype('str').str.split('-').str[0] # 연도 컬럼 생성
    df_pivot_dividends = pd.pivot_table(df_dividends, values="Dividends", index="Year", aggfunc='sum') # 배당금 피벗 테이블 생성_연도별 배당금

    # 종가 테이블, 배당금 테이블 join 하기
    df_merged = pd.merge(left=df_pivot_price, right=df_pivot_dividends, left_index=True, right_index=True, how="inner") # 인덱스로 join 하기
    df_merged["Dividends yield rate"] = round((df_merged["Dividends"]/df_merged[ticker+"_closed"])*100, 1) # 배당률 컬럼 생성

    # 엑셀 파일에 시트로 저장
    df_result_list.append(df_merged) # 각 종목별 만들어진 결과물 데이터프레임을 리스트에 모아준다.

    # 시각화
    plot_data(df_merged, ticker)
```
\- 필요에 따라 DIR_SAVEFILE과 DIR_DIVIDEND_ARISTOCRAT의 경로를 수정한다. 각각 결과물을 저장할 경로와 [배당귀족주 리스트 안내 블로그](https://blog.naver.com/polarisians/223609374301) 에서 수집한 배당귀족주 리스트 엑셀 파일을 불러올 경로이다.  


### 2-2-4. 함수들 실행 및 결과물 데이터프레임을 엑셀 파일로 저장
```
# 반복문으로 모든 종목에 대해 결과물 저장하고 시각화하기
for t in lst_dividend_aristocrats: # 배당귀족주 리스트의 티커들
    scraping_stock_data(t) # 데이터프레임 시각화, 데이터프레임 저장

# 데이터프레임들 각 시트에 저장
with pd.ExcelWriter(DIR_SAVEFILE) as writer:
    for i in range(len(df_result_list)):
        df_result_list[i].to_excel(writer, sheet_name=lst_dividend_aristocrats[i])
```    

# 3. 결과물  

![image](https://github.com/user-attachments/assets/e9baa2ea-5022-4177-a70e-56d4aea20748)  
![image](https://github.com/user-attachments/assets/f75a1305-57f7-427f-b696-ced241010e5e)  
\- 위 두 종목 외에도 다른 배당귀족주들에 대해 배당률, 배당금을 그래프로 확인할 수 있으며, 결과물은 엑셀 파일로 저장된다.
