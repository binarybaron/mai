from typing import Dict, List
from llm import call_llm
from config import TARGET_USER


class WeeklyAnalyzer:
    """Analyzes weekly conversation data using LLM"""

    def __init__(self, target_user: str = TARGET_USER):
        self.target_user = target_user

    def analyze_week(self, week_data: Dict) -> str:
        """
        Analyze a week's conversations to understand the target user's emotional state.

        Args:
            week_data: Dictionary containing week information and conversations

        Returns:
            Analysis summary as a string
        """
        week_key = week_data["week_key"]
        conversations = week_data["conversations"]
        target_count = week_data["target_message_count"]

        if target_count == 0:
            return f"No messages from {self.target_user} this week."

        # Combine all conversations for this week
        all_conversations = "\n\n---\n\n".join(conversations)

        # Create prompt for LLM
        prompt = f"""You are analyzing WhatsApp chat conversations to understand how {self.target_user} was feeling during a specific week.

Week: {week_key}
Number of messages from {self.target_user}: {target_count}

Here are the conversation snippets involving {self.target_user} from that week:

{all_conversations}

Please provide a detailed summary of this week for {self.target_user}. Include:

1. How did {self.target_user} feel? (emotional state, mood indicators)
2. What bad things happened? (problems, conflicts, negative events)
3. What good things happened? (positive events, happy moments, social interactions)
4. Was she depressed? (signs of low mood, withdrawal, negative self-talk)
5. Was she happy? (signs of joy, excitement, positive engagement)
6. Was she manic? (signs of elevated mood, high energy, impulsive behavior)

IMPORTANT:
- Include relevant direct quotes from {self.target_user}'s messages to support your observations
- DO NOT hallucinate or invent things that are not in the messages
- DO NOT interpret or add meaning - just summarize what is actually said
- Be specific and detailed
- If you cannot determine something from the messages, say so
- Focus on factual observations from the text

Format your response as a structured summary."""

        # Call LLM
        analysis = call_llm(prompt)

        return analysis

    def analyze_all_weeks(self, weeks_data: Dict[str, Dict]) -> Dict[str, str]:
        """
        Analyze all weeks.

        Args:
            weeks_data: Dictionary mapping week keys to week data

        Returns:
            Dictionary mapping week keys to analysis summaries
        """
        analyses = {}

        print(f"\nAnalyzing {len(weeks_data)} weeks...")

        for week_key in sorted(weeks_data.keys()):
            print(f"  Analyzing {week_key}...")
            week_data = weeks_data[week_key]
            analysis = self.analyze_week(week_data)
            analyses[week_key] = analysis

        return analyses


class SentimentAnalyzer:
    """Performs sentiment analysis across all weekly summaries"""

    def __init__(self, target_user: str = TARGET_USER):
        self.target_user = target_user

    def analyze_sentiment(self, weekly_analyses: Dict[str, str]) -> Dict[str, float]:
        """
        Analyze sentiment across all weeks.

        Args:
            weekly_analyses: Dictionary mapping week keys to analysis summaries

        Returns:
            Dictionary mapping week keys to sentiment scores (0-10, 0=happy, 10=depressed)
        """
        sentiment_scores = {}

        print(f"\nPerforming sentiment analysis on {len(weekly_analyses)} weeks...")

        for week_key in sorted(weekly_analyses.keys()):
            print(f"  Scoring {week_key}...")
            analysis = weekly_analyses[week_key]

            # Skip empty weeks
            if "No messages from" in analysis:
                continue

            prompt = f"""You are analyzing the emotional state of {self.target_user} based on a weekly summary of their conversations.

Here is the weekly summary:

{analysis}

Based on this summary, rate {self.target_user}'s overall emotional state for this week on a scale from 0 to 10:
- 0 = Very happy, positive, thriving
- 5 = Neutral, balanced mood
- 10 = Very depressed, negative, struggling

Consider factors like:
- Overall emotional tone
- Presence of negative vs positive events
- Social engagement and connections
- Signs of depression, anxiety, or distress
- Signs of happiness, excitement, or mania

Respond with ONLY a number between 0 and 10 (you can use decimals like 6.5).
Do not include any explanation, just the number."""

            try:
                score_text = call_llm(prompt).strip()
                # Extract the number from the response
                score = float(score_text.split()[0].replace(',', '.'))
                # Clamp to 0-10 range
                score = max(0.0, min(10.0, score))
                sentiment_scores[week_key] = score
            except (ValueError, IndexError) as e:
                print(f"  Warning: Could not parse score for {week_key}: {e}")
                sentiment_scores[week_key] = 5.0  # Default to neutral

        return sentiment_scores

    def generate_overall_summary(self, weekly_analyses: Dict[str, str], sentiment_scores: Dict[str, float]) -> str:
        """
        Generate an overall summary across all weeks.

        Args:
            weekly_analyses: Dictionary mapping week keys to analysis summaries
            sentiment_scores: Dictionary mapping week keys to sentiment scores

        Returns:
            Overall summary text
        """
        # Combine all weekly analyses
        all_analyses = []
        for week_key in sorted(weekly_analyses.keys()):
            score = sentiment_scores.get(week_key, "N/A")
            all_analyses.append(f"=== {week_key} (Score: {score}) ===\n{weekly_analyses[week_key]}")

        combined = "\n\n".join(all_analyses)

        prompt = f"""You have been analyzing {self.target_user}'s emotional state over multiple weeks based on WhatsApp conversations.

Here are all the weekly summaries with their sentiment scores (0=happy, 10=depressed):

{combined}

Please provide an overall summary that includes:

1. General emotional trajectory over time (improving, declining, stable, fluctuating)
2. Common themes and patterns
3. Key events or periods of concern
4. Key events or periods of joy
5. Overall assessment of {self.target_user}'s well-being during this period

Be specific and reference particular weeks when relevant."""

        overall_summary = call_llm(prompt)

        return overall_summary
