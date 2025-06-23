# pandas_data_analyzer.py - 直接查询版本（替换原文件）
import pandas as pd
import numpy as np
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQueryEngine:
    """直接数据查询引擎 - 绕过pandas agent"""
    
    def __init__(self, stock_data, news_data, earnings_data, cashflow_data):
        self.stock_data = stock_data
        self.news_data = news_data
        self.earnings_data = earnings_data
        self.cashflow_data = cashflow_data
        
        # 标准化列名映射
        self.stock_cols = {
            'symbol': 'symbol',
            'date': 'date', 
            'open': '1. open',
            'high': '2. high',
            'low': '3. low',
            'close': '4. close',
            'volume': '5. volume'
        }
        
        # 预处理数据
        self._preprocess_data()
    
    def _preprocess_data(self):
        """预处理数据"""
        try:
            # 标准化股票代码为大写
            if 'symbol' in self.stock_data.columns:
                self.stock_data['symbol'] = self.stock_data['symbol'].str.upper()
            
            # 转换日期格式
            if 'date' in self.stock_data.columns:
                self.stock_data['date'] = pd.to_datetime(self.stock_data['date'])
            
            # 获取可用股票列表
            self.available_symbols = self.stock_data['symbol'].unique() if 'symbol' in self.stock_data.columns else []
            
            logger.info(f"Preprocessing completed: {len(self.available_symbols)} stock symbols")
            
        except Exception as e:
            logger.warning(f"Data preprocessing failed: {e}")
    
    def query(self, question):
        """主查询入口"""
        question_lower = question.lower()
        
        # 1. 股价查询
        if any(word in question_lower for word in ['price', 'stock price', 'share price']):
            return self._handle_price_query(question_lower)
        
        # 2. 收益查询
        elif any(word in question_lower for word in ['earnings', 'revenue', 'profit']):
            return self._handle_earnings_query(question_lower)
        
        # 3. 现金流查询
        elif any(word in question_lower for word in ['cash flow', 'cashflow']):
            return self._handle_cashflow_query(question_lower)
        
        # 4. 新闻情绪查询
        elif any(word in question_lower for word in ['sentiment', 'news']):
            return self._handle_sentiment_query(question_lower)
        
        # 5. 统计查询
        elif any(word in question_lower for word in ['average', 'mean', 'median', 'max', 'min', 'highest', 'lowest']):
            return self._handle_stats_query(question_lower)
        
        # 6. 比较查询
        elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'between']):
            return self._handle_comparison_query(question_lower)
        
        # 7. 排名查询
        elif any(word in question_lower for word in ['top', 'best', 'worst', 'rank', 'ranking']):
            return self._handle_ranking_query(question_lower)
        
        # 8. 数据信息查询
        elif any(word in question_lower for word in ['companies', 'symbols', 'available', 'list', 'data summary']):
            return self._handle_info_query(question_lower)
        
        # 9. 默认回退
        else:
            return self._handle_fallback_query(question)
    
    def _handle_price_query(self, question):
        """处理股价查询 - 增强版"""
        try:
            close_col = self.stock_cols['close']
            
            # 特定公司股价 - 提供更详细信息
            company = self._extract_company(question)
            if company:
                company_data = self.stock_data[self.stock_data['symbol'] == company.upper()]
                if not company_data.empty:
                    latest_price = company_data.iloc[-1][close_col]
                    latest_date = company_data.iloc[-1]['date'] if 'date' in company_data.columns else 'recent'
                    
                    # 计算额外统计信息
                    high_col = self.stock_cols['high']
                    low_col = self.stock_cols['low']
                    volume_col = self.stock_cols['volume']
                    
                    latest_high = company_data.iloc[-1][high_col] if high_col in company_data.columns else 'N/A'
                    latest_low = company_data.iloc[-1][low_col] if low_col in company_data.columns else 'N/A'
                    latest_volume = company_data.iloc[-1][volume_col] if volume_col in company_data.columns else 'N/A'
                    
                    # 计算价格统计
                    avg_price = company_data[close_col].mean()
                    price_change_pct = ((latest_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
                    
                    return f"""📈 {company} Stock Analysis:
• Current Price: ${latest_price:.2f} (as of {latest_date})
• Day High: ${latest_high:.2f} | Day Low: ${latest_low:.2f}
• Volume: {latest_volume:,} shares
• Average Price (historical): ${avg_price:.2f}
• Price vs Average: {price_change_pct:+.1f}%
• Total Records: {len(company_data)} data points"""
                else:
                    return f"Sorry, no data found for {company}. Available stocks: {', '.join(self.available_symbols[:10])}"
            
            # 平均股价 - 更详细的市场概况
            elif 'average' in question or 'mean' in question:
                avg_price = self.stock_data[close_col].mean()
                median_price = self.stock_data[close_col].median()
                std_price = self.stock_data[close_col].std()
                total_companies = len(self.available_symbols)
                
                return f"""📊 Market Overview - Average Prices:
• Average Stock Price: ${avg_price:.2f}
• Median Stock Price: ${median_price:.2f}
• Price Standard Deviation: ${std_price:.2f}
• Companies Analyzed: {total_companies}
• Price Range: ${self.stock_data[close_col].min():.2f} - ${self.stock_data[close_col].max():.2f}"""
            
            # 最高/最低股价 - 包含更多上下文
            elif 'highest' in question or 'max' in question:
                max_price = self.stock_data[close_col].max()
                max_idx = self.stock_data[close_col].idxmax()
                max_company = self.stock_data.loc[max_idx, 'symbol']
                max_date = self.stock_data.loc[max_idx, 'date'] if 'date' in self.stock_data.columns else 'N/A'
                
                # 找到前5名最高价格
                top_5_prices = self.stock_data.groupby('symbol')[close_col].max().sort_values(ascending=False).head(5)
                top_5_list = [f"{symbol}: ${price:.2f}" for symbol, price in top_5_prices.items()]
                
                return f"""🏆 Highest Stock Prices:
• #1 Highest: ${max_price:.2f} ({max_company}) on {max_date}

Top 5 Highest Prices:
{chr(10).join(f'{i+1}. {price}' for i, price in enumerate(top_5_list))}"""
            
            elif 'lowest' in question or 'min' in question:
                min_price = self.stock_data[close_col].min()
                min_idx = self.stock_data[close_col].idxmin()
                min_company = self.stock_data.loc[min_idx, 'symbol']
                min_date = self.stock_data.loc[min_idx, 'date'] if 'date' in self.stock_data.columns else 'N/A'
                
                # 找到最低5名价格
                bottom_5_prices = self.stock_data.groupby('symbol')[close_col].min().sort_values().head(5)
                bottom_5_list = [f"{symbol}: ${price:.2f}" for symbol, price in bottom_5_prices.items()]
                
                return f"""📉 Lowest Stock Prices:
• #1 Lowest: ${min_price:.2f} ({min_company}) on {min_date}

Bottom 5 Lowest Prices:
{chr(10).join(f'{i+1}. {price}' for i, price in enumerate(bottom_5_list))}"""
            
            else:
                return "Please specify which company you're asking about, e.g., 'What is Apple stock price?'"
                
        except Exception as e:
            logger.error(f"Price query failed: {e}")
            return "Sorry, unable to retrieve stock price information."
    
    def _handle_earnings_query(self, question):
        """处理收益查询"""
        try:
            if self.earnings_data.empty:
                return "Sorry, no earnings data currently available."
            
            company = self._extract_company(question)
            if company:
                company_earnings = self.earnings_data[self.earnings_data['symbol'].str.upper() == company.upper()]
                if not company_earnings.empty:
                    latest = company_earnings.iloc[-1]
                    return f"{company} latest earnings:\n• Reported EPS: {latest.get('reportedEPS', 'N/A')}\n• Estimated EPS: {latest.get('estimatedEPS', 'N/A')}\n• Report Date: {latest.get('reportedDate', 'N/A')}"
                else:
                    available = self.earnings_data['symbol'].unique()[:10]
                    return f"No earnings data found for {company}. Available companies: {', '.join(available)}"
            else:
                # 显示总体收益摘要
                avg_eps = self.earnings_data['reportedEPS'].mean() if 'reportedEPS' in self.earnings_data.columns else 0
                return f"Earnings data summary:\n• Average EPS: {avg_eps:.2f}\n• Records: {len(self.earnings_data)}\n• Companies covered: {len(self.earnings_data['symbol'].unique())}"
                
        except Exception as e:
            logger.error(f"Earnings query failed: {e}")
            return "Sorry, unable to retrieve earnings information."
    
    def _handle_cashflow_query(self, question):
        """处理现金流查询"""
        try:
            if self.cashflow_data.empty:
                return "Sorry, no cash flow data currently available."
            
            company = self._extract_company(question)
            if company:
                company_cf = self.cashflow_data[self.cashflow_data['symbol'].str.upper() == company.upper()]
                if not company_cf.empty:
                    latest = company_cf.iloc[-1]
                    return f"{company} latest cash flow:\n• Operating Cash Flow: {latest.get('operatingCashflow', 'N/A')}\n• Investment Cash Flow: {latest.get('cashflowFromInvestment', 'N/A')}\n• Financing Cash Flow: {latest.get('cashflowFromFinancing', 'N/A')}"
                else:
                    available = self.cashflow_data['symbol'].unique()[:10]
                    return f"No cash flow data found for {company}. Available companies: {', '.join(available)}"
            else:
                return f"Cash flow data summary:\n• Records: {len(self.cashflow_data)}\n• Companies covered: {len(self.cashflow_data['symbol'].unique())}"
                
        except Exception as e:
            logger.error(f"Cash flow query failed: {e}")
            return "Sorry, unable to retrieve cash flow information."
    
    def _handle_sentiment_query(self, question):
        """处理情绪查询"""
        try:
            if self.news_data.empty:
                return "Sorry, no news sentiment data currently available."
            
            if 'sentiment_score' in self.news_data.columns:
                avg_sentiment = self.news_data['sentiment_score'].mean()
                sentiment_label = "Positive" if avg_sentiment > 0 else "Negative" if avg_sentiment < 0 else "Neutral"
                
                return f"News sentiment analysis:\n• Average sentiment score: {avg_sentiment:.3f} ({sentiment_label})\n• News articles: {len(self.news_data)}\n• Time range: {self.news_data['time_published'].min() if 'time_published' in self.news_data.columns else 'N/A'} to {self.news_data['time_published'].max() if 'time_published' in self.news_data.columns else 'N/A'}"
            else:
                return f"News data summary:\n• Articles: {len(self.news_data)}\n• Columns: {', '.join(self.news_data.columns)}"
                
        except Exception as e:
            logger.error(f"Sentiment query failed: {e}")
            return "Sorry, unable to retrieve sentiment analysis information."
    
    def _handle_stats_query(self, question):
        """处理统计查询"""
        try:
            close_col = self.stock_cols['close']
            
            if 'average' in question or 'mean' in question:
                avg_price = self.stock_data[close_col].mean()
                return f"Average stock price: ${avg_price:.2f}"
            
            elif 'median' in question:
                median_price = self.stock_data[close_col].median()
                return f"Median stock price: ${median_price:.2f}"
            
            elif 'max' in question or 'highest' in question:
                max_price = self.stock_data[close_col].max()
                return f"Highest stock price: ${max_price:.2f}"
            
            elif 'min' in question or 'lowest' in question:
                min_price = self.stock_data[close_col].min()
                return f"Lowest stock price: ${min_price:.2f}"
            
            else:
                stats = self.stock_data[close_col].describe()
                return f"Stock price statistics:\n• Average: ${stats['mean']:.2f}\n• Median: ${stats['50%']:.2f}\n• Highest: ${stats['max']:.2f}\n• Lowest: ${stats['min']:.2f}"
                
        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            return "Sorry, unable to calculate statistics."
    
    def _handle_comparison_query(self, question):
        """处理比较查询 - 增强版"""
        try:
            # 检查是否要求更多方面的比较
            detailed_analysis = any(word in question.lower() for word in 
                                  ['more', 'detailed', 'comprehensive', 'full', 'complete', 'aspect', 'detail'])
            
            companies = self._extract_multiple_companies(question)
            if len(companies) >= 2:
                close_col = self.stock_cols['close']
                high_col = self.stock_cols['high']
                low_col = self.stock_cols['low']
                volume_col = self.stock_cols['volume']
                
                results = []
                
                for company in companies[:3]:  # 最多比较3家
                    company_data = self.stock_data[self.stock_data['symbol'] == company.upper()]
                    if not company_data.empty:
                        latest_price = company_data.iloc[-1][close_col]
                        
                        if detailed_analysis:
                            # 详细比较
                            avg_price = company_data[close_col].mean()
                            latest_high = company_data.iloc[-1][high_col] if high_col in company_data.columns else 'N/A'
                            latest_low = company_data.iloc[-1][low_col] if low_col in company_data.columns else 'N/A'
                            latest_volume = company_data.iloc[-1][volume_col] if volume_col in company_data.columns else 'N/A'
                            
                            # 获取收益数据（如果有）
                            earnings_info = ""
                            if not self.earnings_data.empty and 'symbol' in self.earnings_data.columns:
                                company_earnings = self.earnings_data[self.earnings_data['symbol'] == company.upper()]
                                if not company_earnings.empty:
                                    latest_eps = company_earnings.iloc[-1].get('reportedEPS', 'N/A')
                                    earnings_info = f"\n  📊 Latest EPS: {latest_eps}"
                            
                            # 获取现金流数据（如果有）
                            cashflow_info = ""
                            if not self.cashflow_data.empty and 'symbol' in self.cashflow_data.columns:
                                company_cf = self.cashflow_data[self.cashflow_data['symbol'] == company.upper()]
                                if not company_cf.empty:
                                    operating_cf = company_cf.iloc[-1].get('operatingCashflow', 'N/A')
                                    cashflow_info = f"\n  💰 Operating Cash Flow: {operating_cf}"
                            
                            results.append(f"""📈 {company} Analysis:
  💵 Current Price: ${latest_price:.2f}
  📊 Average Price: ${avg_price:.2f}
  📈 Day High: ${latest_high:.2f} | 📉 Day Low: ${latest_low:.2f}
  📦 Volume: {latest_volume:,} shares{earnings_info}{cashflow_info}""")
                        else:
                            # 简单比较
                            results.append(f"• {company}: ${latest_price:.2f}")
                
                if results:
                    if detailed_analysis:
                        return f"🔍 Comprehensive Company Comparison:\n\n" + "\n\n".join(results)
                    else:
                        return f"📊 Stock Price Comparison:\n" + "\n".join(results)
                else:
                    return "Sorry, unable to find data for the specified companies."
            else:
                return "Please specify companies to compare, e.g., 'Compare Apple and Microsoft stock prices'"
                
        except Exception as e:
            logger.error(f"Comparison query failed: {e}")
            return "Sorry, unable to perform comparison analysis."
    
    def _handle_ranking_query(self, question):
        """处理排名查询"""
        try:
            close_col = self.stock_cols['close']
            
            # 获取每个公司的最新股价
            latest_prices = self.stock_data.groupby('symbol')[close_col].last().sort_values(ascending=False)
            
            if 'top' in question:
                n = self._extract_number(question) or 5
                top_companies = latest_prices.head(n)
                results = [f"{i+1}. {symbol}: ${price:.2f}" for i, (symbol, price) in enumerate(top_companies.items())]
                return f"Top {n} highest stock prices:\n" + "\n".join(results)
            
            elif 'worst' in question or 'lowest' in question:
                n = self._extract_number(question) or 5
                bottom_companies = latest_prices.tail(n)
                results = [f"{i+1}. {symbol}: ${price:.2f}" for i, (symbol, price) in enumerate(reversed(bottom_companies.items()))]
                return f"{n} lowest stock prices:\n" + "\n".join(results)
            
            else:
                # 默认显示前5名
                top_5 = latest_prices.head(5)
                results = [f"{i+1}. {symbol}: ${price:.2f}" for i, (symbol, price) in enumerate(top_5.items())]
                return f"Top 5 companies by stock price:\n" + "\n".join(results)
                
        except Exception as e:
            logger.error(f"Ranking query failed: {e}")
            return "Sorry, unable to generate ranking information."
    
    def _handle_info_query(self, question):
        """处理信息查询"""
        try:
            if 'companies' in question or 'symbols' in question:
                symbols = sorted(self.available_symbols)
                return f"Available stock symbols ({len(symbols)} total):\n{', '.join(symbols[:20])}{'...' if len(symbols) > 20 else ''}"
            
            elif 'summary' in question:
                return f"Data summary:\n• Stock data: {len(self.stock_data)} records, {len(self.available_symbols)} companies\n• News data: {len(self.news_data)} records\n• Earnings data: {len(self.earnings_data)} records\n• Cash flow data: {len(self.cashflow_data)} records"
            
            else:
                return f"System contains data for {len(self.available_symbols)} companies, including stock prices, earnings, cash flow, and news sentiment information."
                
        except Exception as e:
            logger.error(f"Info query failed: {e}")
            return "Sorry, unable to retrieve data information."
    
    def _handle_fallback_query(self, question):
        """处理回退查询"""
        return f"Sorry, I can't process this query: '{question}'.\n\nI can help you with:\n• Stock prices: 'What is Apple stock price?'\n• Company comparisons: 'Compare Apple and Microsoft'\n• Rankings: 'Top 5 companies by stock price'\n• Data summary: 'Show me data summary'"
    
    def _extract_company(self, question):
        """从问题中提取公司名"""
        # 常见公司名映射
        company_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT', 
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'nvidia': 'NVDA',
            'netflix': 'NFLX',
            'adobe': 'ADBE',
            'salesforce': 'CRM',
            'oracle': 'ORCL'
        }
        
        for name, symbol in company_map.items():
            if name in question.lower():
                return symbol
        
        # 检查是否直接提到了股票代码
        for symbol in self.available_symbols:
            if symbol.lower() in question.lower():
                return symbol
        
        return None
    
    def _extract_multiple_companies(self, question):
        """从问题中提取多个公司"""
        companies = []
        
        # 尝试提取常见公司
        company_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT', 
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA'
        }
        
        for name, symbol in company_map.items():
            if name in question.lower():
                companies.append(symbol)
        
        return companies
    
    def _extract_number(self, question):
        """从问题中提取数字"""
        import re
        numbers = re.findall(r'\d+', question)
        return int(numbers[0]) if numbers else None

# 全局变量
stock_data = None
news_data = None
earnings_data = None
cashflow_data = None
query_engine = None

def load_and_prepare_data():
    """加载和预处理数据"""
    global stock_data, news_data, earnings_data, cashflow_data, query_engine
    
    try:
        # 加载数据
        stock_data = pd.read_csv("./data/stock_weekly_data.csv")
        news_data = pd.read_csv("./data/news_sentiment.csv")
        earnings_data = pd.read_csv("./data/quarterly_earnings.csv")
        cashflow_data = pd.read_csv("./data/cash_flow.csv")
        
        # 数据清理
        if 'symbol' in stock_data.columns:
            stock_data['symbol'] = stock_data['symbol'].str.upper()
        
        # 🚀 创建直接查询引擎
        query_engine = DataQueryEngine(stock_data, news_data, earnings_data, cashflow_data)
        
        logger.info("📊 Data loaded successfully:")
        logger.info(f"Stock data: {stock_data.shape}")
        logger.info(f"Available symbols: {sorted(stock_data['symbol'].unique()[:10])}")
        logger.info("✅ Direct query engine created")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        return False

def run_analytical_query(query):
    """运行分析查询 - 使用直接查询引擎"""
    try:
        logger.info(f"🔍 Processing query: {query}")
        
        if query_engine is None:
            return "Data analysis system not initialized. Please try again later."
        
        # 🚀 使用直接查询引擎
        result = query_engine.query(query)
        
        if result:
            logger.info("✅ Direct query successful")
            return result
        else:
            return "Sorry, I couldn't process that query. Please try asking about stock prices, earnings, or company information."
            
    except Exception as e:
        logger.error(f"❌ Query processing failed: {e}")
        return f"Sorry, an error occurred while processing your query: {str(e)}"

def initialize_system():
    """初始化系统"""
    logger.info("🚀 Initializing direct query system...")
    
    if not load_and_prepare_data():
        logger.error("❌ System initialization failed")
        return False
    
    logger.info("✅ System initialization complete")
    return True

# 在模块加载时初始化
if __name__ == "__main__":
    if initialize_system():
        # 测试查询
        test_queries = [
            "What is Apple stock price?",
            "Show me the highest stock price",
            "Compare Apple and Microsoft",
            "What companies are available?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            result = run_analytical_query(query)
            print(f"📝 Result: {result}")
    else:
        print("❌ System initialization failed")
else:
    initialize_system()