from django.db import models


class User(models.Model):
    GENDER_CHOICES = [('male', 'male'), ('female', 'female')]
    ROLE_CHOICES = [('user', 'user'), ('admin', 'admin')]

    nickname = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.nickname


class HairStyle(models.Model):
    hair_code = models.CharField(max_length=5, null=True, blank=True)
    style_name = models.CharField(max_length=100)
    image_url = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'hair_styles'

    def __str__(self):
        return self.style_name


class MakeupStyle(models.Model):
    style_code = models.CharField(max_length=20, null=True, blank=True, unique=True)
    style_name = models.CharField(max_length=100)
    image_url = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'makeup_styles'

    def __str__(self):
        return self.style_name


class AnalysisSession(models.Model):
    FACE_SHAPE_CHOICES = [
        ('oval', 'oval'), ('round', 'round'), ('square', 'square'),
        ('oblong', 'oblong'), ('heart', 'heart'),
    ]
    FACE_POINT_CHOICES = [
        ('upper', 'upper'), ('middle', 'middle'),
        ('lower', 'lower'), ('golden', 'golden'),
    ]
    SKIN_TONE_CHOICES = [
        ('spring', 'spring'), ('summer', 'summer'),
        ('fall', 'fall'), ('winter', 'winter'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_sessions')
    image_path = models.CharField(max_length=500)

    face_shape = models.CharField(max_length=10, choices=FACE_SHAPE_CHOICES, null=True, blank=True)
    face_point = models.CharField(max_length=10, choices=FACE_POINT_CHOICES, null=True, blank=True)
    skin_tone = models.CharField(max_length=10, choices=SKIN_TONE_CHOICES, null=True, blank=True)

    skin_lab_b = models.FloatField(null=True, blank=True)

    ratio_face_wh = models.FloatField(null=True, blank=True)
    ratio_jaw_cheek = models.FloatField(null=True, blank=True)
    ratio_forehead_cheek = models.FloatField(null=True, blank=True)

    ratio_upper_third = models.FloatField(null=True, blank=True)
    ratio_middle_third = models.FloatField(null=True, blank=True)
    ratio_lower_third = models.FloatField(null=True, blank=True)

    result = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analysis_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Session [{self.user.nickname}] - {self.created_at.strftime('%Y-%m-%d')}"


class StyleMappingList(models.Model):
    TYPE_CHOICES = [('hair', 'hair'), ('makeup', 'makeup'), ('ootd', 'ootd')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='style_mappings')
    analysis_session = models.ForeignKey(
        AnalysisSession, on_delete=models.CASCADE, related_name='style_mappings'
    )

    type = models.CharField(max_length=6, choices=TYPE_CHOICES)

    hair_style = models.ForeignKey(
        HairStyle, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='style_mappings'
    )
    makeup_style = models.ForeignKey(
        MakeupStyle, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='style_mappings'
    )

    style_name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'style_mapping_list'

    def __str__(self):
        return f"{self.type} - {self.style_name}"


class SimulationResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulation_results')
    analysis_session = models.ForeignKey(
        AnalysisSession, on_delete=models.CASCADE, related_name='simulation_results'
    )

    hair_mapping = models.ForeignKey(
        StyleMappingList, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hair_results'
    )
    makeup_mapping = models.ForeignKey(
        StyleMappingList, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='makeup_results'
    )

    generated_image_path = models.CharField(max_length=500, null=True, blank=True)
    is_saved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simulation_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"Simulation [{self.user.nickname}] - {self.created_at.strftime('%Y-%m-%d')}"


class UserFeedback(models.Model):
    TARGET_TYPE_CHOICES = [('hair', 'hair'), ('makeup', 'makeup')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    simulation_result = models.ForeignKey(
        SimulationResult, on_delete=models.SET_NULL,
        related_name='feedbacks', null=True, blank=True
    )

    target_type = models.CharField(max_length=6, choices=TARGET_TYPE_CHOICES)
    user_chat = models.TextField(null=True, blank=True)
    ai_chat = models.TextField(null=True, blank=True)
    img_url = models.CharField(max_length=100, null=True, blank=True)
    applied_style_key = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_feedback'

    def __str__(self):
        return f"{self.target_type} feedback by {self.user.nickname}"
