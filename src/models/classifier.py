"""Message classification for Slack text."""

import re

import mlflow
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.models.preprocessing import prepare_text_frame

TECH_KEYWORDS = {
    'python', 'sql', 'docker', 'kubernetes', 'api', 'git', 'github', 'model',
    'machine', 'learning', 'data', 'pipeline', 'error', 'code', 'function',
    'database', 'postgres', 'mongodb', 'aws', 'terraform', 'pytest', 'pandas',
    'numpy', 'kafka', 'mlflow', 'algorithm', 'deploy', 'server', 'bug',
}

QUESTION_STARTS = ('how', 'what', 'why', 'when', 'where', 'who', 'can', 'could', 'is', 'are', 'does')


def is_technical(text):
    """Heuristic check for technical content."""
    tokens = set(re.findall(r'[a-z0-9]+', text.lower()))
    return bool(tokens & TECH_KEYWORDS) or '```' in text or 'import ' in text


def weak_label_message(row):
    """
    Assign a weak label using simple rules.

    Tags: Question-Technical, Question-Non-technical, Comment-Technical,
    Comment-Non-Technical, Answer, Other.
    """
    text = str(row.get('text', '')).strip()
    clean = text.lower()
    technical = is_technical(text)

    if '?' in text or clean.startswith(QUESTION_STARTS):
        prefix = 'Question'
    elif row.get('replies_to') or row.get('parent_user_id'):
        prefix = 'Answer'
    elif len(clean.split()) <= 3:
        prefix = 'Other'
    else:
        prefix = 'Comment'

    if prefix == 'Answer':
        return 'Answer'
    if prefix == 'Other':
        return 'Other'
    if prefix == 'Question':
        return 'Question-Technical' if technical else 'Question-Non-technical'
    return 'Comment-Technical' if technical else 'Comment-Non-Technical'


def build_labeled_frame(df):
    """Return dataframe with weak labels for modelling."""
    labeled = prepare_text_frame(df)
    labeled['label'] = labeled.apply(weak_label_message, axis=1)
    return labeled


def train_message_classifier(df, experiment_name='slack-message-classifier'):
    """
    Train a TF-IDF + logistic regression classifier and log with MLflow.

    Returns:
        Tuple of (pipeline, labeled dataframe, metrics dict).
    """
    labeled = build_labeled_frame(df)
    if labeled['label'].nunique() < 2:
        raise ValueError('Need at least two classes to train the classifier.')

    x_train, x_test, y_train, y_test = train_test_split(
        labeled['clean_text'],
        labeled['label'],
        test_size=0.2,
        random_state=42,
        stratify=labeled['label'] if labeled['label'].value_counts().min() >= 2 else None,
    )

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf', LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    report = classification_report(y_test, predictions, output_dict=True)

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name='message_classifier'):
        mlflow.log_param('train_size', len(x_train))
        mlflow.log_param('num_classes', labeled['label'].nunique())
        mlflow.log_metric('accuracy', report['accuracy'])
        mlflow.sklearn.log_model(pipeline, 'message_classifier')

    return pipeline, labeled, report


def predict_message_labels(pipeline, df):
    """Predict message labels for new messages."""
    prepared = prepare_text_frame(df)
    prepared['predicted_label'] = pipeline.predict(prepared['clean_text'])
    return prepared
