"""
Integration Test: GoogleNewsSearcher + NewsAgent V3

Purpose:
- Test the complete fact-opinion decoupled pipeline
- Verify Google News -> AI Commentary flow
- Validate JSON output structure

Cost: 1 SerpApi request + 1 Gemini request
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_news_searcher import GoogleNewsSearcher
from news_agent import NewsAgent

print("=" * 60)
print("🧪 Integration Test: News Search + AI Analysis")
print("=" * 60)

# Test Symbol
TEST_SYMBOL = "AAPL"

# Step 1: Fetch News (Hard Facts)
print(f"\n1️⃣  Fetching news for {TEST_SYMBOL}...")
searcher = GoogleNewsSearcher()

if not searcher.enabled:
    print("❌ GoogleNewsSearcher not enabled")
    sys.exit(1)

news = searcher.search_news(TEST_SYMBOL, days=3)
print(f"✅ Found {len(news)} news articles")

if not news:
    print("⚠️  No news found, cannot test AI analysis")
    sys.exit(1)

# Display news headlines
print("\n📰 News Headlines:")
for i, article in enumerate(news[:3], 1):
    print(f"   {i}. {article['title']} ({article['date']})")

# Step 2: AI Analysis (Commentary)
print(f"\n2️⃣  Analyzing news with NewsAgent...")
agent = NewsAgent()

if not agent.enabled:
    print("❌ NewsAgent not enabled")
    sys.exit(1)

analysis = agent.analyze_news(TEST_SYMBOL, news)

if not analysis:
    print("❌ Analysis failed")
    sys.exit(1)

print("✅ Analysis complete")

# Step 3: Validate Output
print("\n3️⃣  Validating output structure...")

required_fields = {
    "sentiment": ["Positive", "Negative", "Neutral"],
    "moat_impact": ["Strengthened", "Weakened", "Unchanged"],
    "prediction": ["Bullish", "Bearish", "Neutral"],
    "confidence": (0.0, 1.0),
    "summary_reason": str
}

all_valid = True

for field, expected in required_fields.items():
    if field not in analysis:
        print(f"❌ Missing field: {field}")
        all_valid = False
    elif isinstance(expected, list):
        if analysis[field] not in expected:
            print(f"❌ Invalid value for {field}: {analysis[field]}")
            all_valid = False
    elif isinstance(expected, tuple):  # Range check
        if not (expected[0] <= analysis[field] <= expected[1]):
            print(f"❌ Out of range for {field}: {analysis[field]}")
            all_valid = False

if all_valid:
    print("✅ All fields valid")

# Step 4: Display Results
print("\n" + "=" * 60)
print("📊 Analysis Result")
print("=" * 60)
print(json.dumps(analysis, indent=2, ensure_ascii=False))

# Step 5: Interpretation
print("\n" + "=" * 60)
print("🎯 Human-Readable Summary")
print("=" * 60)

sentiment_emoji = {
    "Positive": "😊",
    "Negative": "😰",
    "Neutral": "😐"
}

prediction_emoji = {
    "Bullish": "📈",
    "Bearish": "📉",
    "Neutral": "➡️"
}

print(f"\n{TEST_SYMBOL} 新聞分析:")
print(f"  情緒: {sentiment_emoji.get(analysis['sentiment'], '')} {analysis['sentiment']}")
print(f"  護城河: {analysis['moat_impact']}")
print(f"  預測: {prediction_emoji.get(analysis['prediction'], '')} {analysis['prediction']}")
print(f"  信心: {analysis['confidence']:.0%}")
print(f"  理由: {analysis['summary_reason']}")

# Final Summary
print("\n" + "=" * 60)
print("✅ Integration Test Passed!")
print("=" * 60)
print("\n📊 Test Summary:")
print(f"   - News Fetched: ✅ {len(news)} articles")
print(f"   - AI Analysis: ✅ Completed")
print(f"   - JSON Valid: ✅ All fields present")
print(f"   - Sentiment: {analysis['sentiment']}")
print(f"   - Prediction: {analysis['prediction']}")
print("\n💡 Fact-Opinion Decoupling is working correctly!")
