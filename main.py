#!/usr/bin/env python3
"""
Mood Board - WhatsApp Chat Analysis

This script analyzes WhatsApp chat exports to understand a user's emotional
state over time using LLM-based analysis.
"""

import os
import json
from datetime import datetime
from archive_processor import ArchiveProcessor
from week_grouper import WeekGrouper
from analyzer import WeeklyAnalyzer, SentimentAnalyzer
from config import TARGET_USER


def save_results(weekly_analyses: dict, sentiment_scores: dict, overall_summary: str, output_dir: str = "output"):
    """
    Save analysis results to files.

    Args:
        weekly_analyses: Dictionary of weekly analysis summaries
        sentiment_scores: Dictionary of sentiment scores
        overall_summary: Overall summary text
        output_dir: Directory to save results
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save weekly analyses
    with open(os.path.join(output_dir, "weekly_analyses.json"), "w", encoding="utf-8") as f:
        json.dump(weekly_analyses, f, indent=2, ensure_ascii=False)

    # Save sentiment scores
    with open(os.path.join(output_dir, "sentiment_scores.json"), "w", encoding="utf-8") as f:
        json.dump(sentiment_scores, f, indent=2, ensure_ascii=False)

    # Save overall summary
    with open(os.path.join(output_dir, "overall_summary.txt"), "w", encoding="utf-8") as f:
        f.write(overall_summary)

    # Create a combined report
    report = []
    report.append(f"Mood Board Analysis Report for {TARGET_USER}")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Weekly summaries with scores
    report.append("WEEKLY SUMMARIES")
    report.append("=" * 80)
    report.append("")

    for week_key in sorted(weekly_analyses.keys()):
        score = sentiment_scores.get(week_key, "N/A")
        report.append(f"Week: {week_key}")
        report.append(f"Sentiment Score: {score} (0=happy, 10=depressed)")
        report.append("-" * 80)
        report.append(weekly_analyses[week_key])
        report.append("")
        report.append("")

    # Overall summary
    report.append("OVERALL SUMMARY")
    report.append("=" * 80)
    report.append("")
    report.append(overall_summary)

    with open(os.path.join(output_dir, "full_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"\n✓ Results saved to {output_dir}/")


def main():
    """Main execution function"""
    print("=" * 80)
    print("Mood Board - WhatsApp Chat Analysis")
    print("=" * 80)
    print(f"Target user: {TARGET_USER}")
    print("")

    # Step 1: Process all archives and extract messages
    print("[1/5] Processing archives...")
    data_dir = "data"
    processor = ArchiveProcessor()
    all_messages = processor.process_all_archives(data_dir)

    if not all_messages:
        print("Error: No messages found!")
        return

    # Get date range
    min_date = min(msg.timestamp for msg in all_messages)
    max_date = max(msg.timestamp for msg in all_messages)
    print(f"Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

    # Step 2: Group messages by week
    print("\n[2/5] Grouping messages by week...")
    grouper = WeekGrouper(TARGET_USER)
    weeks_data = grouper.get_weekly_summaries(all_messages)
    print(f"Found {len(weeks_data)} weeks")

    # Print summary of each week
    for week_key in sorted(weeks_data.keys()):
        week = weeks_data[week_key]
        print(f"  {week_key}: {week['target_message_count']} messages from {TARGET_USER}, "
              f"{week['total_message_count']} total messages")

    # Step 3: Analyze each week
    print("\n[3/5] Analyzing weekly conversations...")
    analyzer = WeeklyAnalyzer(TARGET_USER)
    weekly_analyses = analyzer.analyze_all_weeks(weeks_data)

    # Step 4: Perform sentiment analysis
    print("\n[4/5] Performing sentiment analysis...")
    sentiment_analyzer = SentimentAnalyzer(TARGET_USER)
    sentiment_scores = sentiment_analyzer.analyze_sentiment(weekly_analyses)

    # Print sentiment scores
    print("\nSentiment Scores (0=happy, 10=depressed):")
    for week_key in sorted(sentiment_scores.keys()):
        score = sentiment_scores[week_key]
        print(f"  {week_key}: {score:.1f}")

    # Step 5: Generate overall summary
    print("\n[5/5] Generating overall summary...")
    overall_summary = sentiment_analyzer.generate_overall_summary(weekly_analyses, sentiment_scores)

    # Save results
    save_results(weekly_analyses, sentiment_scores, overall_summary)

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    print("\nOverall Summary:")
    print("-" * 80)
    print(overall_summary)


if __name__ == "__main__":
    main()
