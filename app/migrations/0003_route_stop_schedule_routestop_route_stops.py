# Generated by Django 5.1.4 on 2025-01-05 02:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_nfccard_remove_user_nfc_id_alter_user_groups_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("ALLER", "Trajet Aller"),
                            ("RETOUR", "Trajet Retour"),
                        ],
                        max_length=10,
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Stop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("order", models.PositiveIntegerField()),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Schedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("departure_time", models.TimeField()),
                ("arrival_time", models.TimeField()),
                (
                    "day_of_week",
                    models.CharField(
                        choices=[
                            ("MON", "Lundi"),
                            ("TUE", "Mardi"),
                            ("WED", "Mercredi"),
                            ("THU", "Jeudi"),
                            ("FRI", "Vendredi"),
                            ("SAT", "Samedi"),
                            ("SUN", "Dimanche"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "route",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.route"
                    ),
                ),
                (
                    "stop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.stop"
                    ),
                ),
            ],
            options={
                "ordering": ["departure_time"],
            },
        ),
        migrations.CreateModel(
            name="RouteStop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.PositiveIntegerField()),
                ("estimated_time", models.IntegerField()),
                (
                    "route",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.route"
                    ),
                ),
                (
                    "stop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.stop"
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
                "unique_together": {("route", "order")},
            },
        ),
        migrations.AddField(
            model_name="route",
            name="stops",
            field=models.ManyToManyField(through="app.RouteStop", to="app.stop"),
        ),
    ]
