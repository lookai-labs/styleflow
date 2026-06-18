from django.db import migrations


NAME_TO_CODE = {
    '코랄 메이크업':      'mk-sp-coral',
    '피치 메이크업':      'mk-sp-peach',
    '주시 메이크업':      'mk-sp-juicy',
    '듀이 메이크업':      'mk-su-dewy',
    '내추럴 메이크업':    'mk-su-natural',
    '로즈 메이크업':      'mk-su-rose',
    '브라운 메이크업':    'mk-au-brown',
    '시크 메이크업':      'mk-au-chic',
    '오피스 메이크업':    'mk-au-office',
    '버건디 메이크업':    'mk-wi-burgundy',
    '글램 메이크업':      'mk-wi-glam',
    '레드 메이크업':      'mk-wi-red',
    '봄웜 내추럴 메이크업':  'mk-m-sp-natural',
    '여름쿨 클린 메이크업':  'mk-m-su-clean',
    '가을웜 소프트 메이크업': 'mk-m-au-soft',
    '겨울쿨 샤프 메이크업':  'mk-m-wi-sharp',
}


def fix_duplicate_styles(apps, schema_editor):
    MakeupStyle = apps.get_model('app', 'MakeupStyle')

    # style_code가 있는 새 row 전부 삭제 (이미 None row가 있으므로)
    MakeupStyle.objects.exclude(style_code=None).delete()

    # 기존 None row에 style_code 채워넣기
    for style_name, style_code in NAME_TO_CODE.items():
        MakeupStyle.objects.filter(style_name=style_name, style_code=None).update(
            style_code=style_code
        )


def reverse_fix(apps, schema_editor):
    MakeupStyle = apps.get_model('app', 'MakeupStyle')
    MakeupStyle.objects.filter(style_code__in=NAME_TO_CODE.values()).update(style_code=None)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_makeup_styles_seed'),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_styles, reverse_code=reverse_fix),
    ]
