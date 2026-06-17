"""Topic modelling for Slack channel text."""

import mlflow
import pandas as pd
from gensim import corpora
from gensim.models import LdaModel
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from src.models.preprocessing import clean_text

STOPWORDS = set(stopwords.words('english'))


def tokenize_for_topics(text):
    """Tokenize cleaned text for LDA."""
    tokens = word_tokenize(clean_text(text))
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def build_channel_corpus(df, channel):
    """Build tokenized documents for one channel."""
    channel_df = df[df['channel'] == channel]
    texts = channel_df['text'].fillna('').astype(str).tolist()
    return [tokenize_for_topics(text) for text in texts if text.strip()]


def train_channel_lda(documents, num_topics=10):
    """
    Train an LDA model for a channel document list.

    Returns:
        Tuple of (lda_model, dictionary).
    """
    dictionary = corpora.Dictionary(documents)
    dictionary.filter_extremes(no_below=2, no_above=0.8)
    corpus = [dictionary.doc2bow(doc) for doc in documents if doc]

    if not corpus:
        return None, dictionary

    lda = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=min(num_topics, max(len(corpus) // 5, 2)),
        random_state=42,
        passes=10,
        alpha='auto',
    )
    return lda, dictionary


def extract_top_topics(lda_model, num_words=8):
    """Return top words for each topic in an LDA model."""
    if lda_model is None:
        return []

    topics = []
    for topic_id in range(lda_model.num_topics):
        words = lda_model.show_topic(topic_id, topn=num_words)
        topics.append({
            'topic_id': topic_id,
            'words': ', '.join(word for word, _ in words),
        })
    return topics


def get_top_topics_by_channel(df, num_topics=10, experiment_name='slack-topic-modelling'):
    """
    Train LDA per channel and return top topics.

    Returns:
        DataFrame with channel, topic_id, and top words.
    """
    rows = []

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name='channel_lda'):
        mlflow.log_param('num_topics', num_topics)

        for channel in sorted(df['channel'].unique()):
            documents = build_channel_corpus(df, channel)
            if len(documents) < 5:
                continue

            lda_model, _ = train_channel_lda(documents, num_topics=num_topics)
            topics = extract_top_topics(lda_model)

            for topic in topics:
                rows.append({
                    'channel': channel,
                    'topic_id': topic['topic_id'],
                    'top_words': topic['words'],
                })

        result = pd.DataFrame(rows)
        mlflow.log_metric('channels_modelled', result['channel'].nunique() if not result.empty else 0)
        if not result.empty:
            mlflow.log_text(result.to_csv(index=False), 'channel_topics.csv')
        return result
