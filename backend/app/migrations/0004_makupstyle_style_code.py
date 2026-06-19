from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_userfeedback_chat_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='makeupstyle',
            name='style_code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
