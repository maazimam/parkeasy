from django import forms
from django.core.validators import RegexValidator


# Existing EmailChangeForm
class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        label="New Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your new email"}
        ),
    )

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        self.user = kwargs.pop("user", None)
        super(EmailChangeForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]

        # Check if email is same as current (only when not adding for the first time)
        if self.user and self.user.email and self.user.email == email:
            raise forms.ValidationError(
                "This is already your current email. Please enter a different email address."
            )

        return email


# New VerificationForm
class VerificationForm(forms.Form):
    age = forms.IntegerField(
        required=True,
        min_value=18,
        max_value=120,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Enter your age"}
        ),
    )

    address = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your full address",
                "rows": 3,
            }
        ),
    )

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = forms.CharField(
        validators=[phone_regex],
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your phone number (e.g., +1234567890)",
            }
        ),
    )

    verification_file = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )

    def clean_verification_file(self):
        file = self.cleaned_data.get("verification_file")
        if file and not file.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are allowed.")
        return file
