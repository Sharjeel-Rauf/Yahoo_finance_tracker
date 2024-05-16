# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']




class TickerSymbolForm(forms.Form):
    ticker_symbol = forms.CharField(label='Ticker symbol', initial='SPY')


class StrategyForm(forms.Form):
    strategy_choices = [('Covered Call', 'Covered Call'), ('Collar', 'Collar'), ('Put Sale', 'Put Sale')]
    strategy = forms.ChoiceField(label='Choose Strategy', choices=strategy_choices)

class TradeDurationForm(forms.Form):
    duration_choices = [
        ("Less than 30 days", "Less than 30 days"),
        ("30-90 days", "30-90 days"),
        ("90+ days", "90+ days")
    ]
    trade_duration = forms.ChoiceField(label="Trade Duration", choices=duration_choices)