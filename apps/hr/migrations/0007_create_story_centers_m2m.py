# Generated manually - Create ManyToMany table for Story.centers

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('centers', '0005_remove_center_address_remove_center_city_and_more'),
        ('hr', '0006_add_thumbnail_image_to_story'),
    ]

    operations = [
        migrations.RunSQL(
            # Create the ManyToMany table if it doesn't exist
            sql="""
                CREATE TABLE IF NOT EXISTS hr_story_centers (
                    id SERIAL PRIMARY KEY,
                    story_id BIGINT NOT NULL REFERENCES hr_story(id) ON DELETE CASCADE,
                    center_id BIGINT NOT NULL REFERENCES centers_center(id) ON DELETE CASCADE,
                    UNIQUE(story_id, center_id)
                );
                CREATE INDEX IF NOT EXISTS hr_story_centers_story_id_idx ON hr_story_centers(story_id);
                CREATE INDEX IF NOT EXISTS hr_story_centers_center_id_idx ON hr_story_centers(center_id);
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS hr_story_centers CASCADE;
            """
        ),
    ]

