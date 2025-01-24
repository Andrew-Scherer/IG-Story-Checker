#!/usr/bin/env python
"""
Database Management Script
Handles database initialization, migrations, and maintenance
"""

import click
from flask.cli import FlaskGroup
from app import create_app
from flask_migrate import Migrate
from models import db, SystemSettings, Niche

def create_cli_app():
    """Create Flask app for CLI commands"""
    app = create_app()
    migrate = Migrate(app, db)
    return app

cli = FlaskGroup(create_app=create_cli_app)

@cli.command('init-db')
def init_db():
    """Initialize database"""
    click.echo('Initializing database...')
    db.create_all()
    click.echo('Database initialized.')

@cli.command('drop-db')
def drop_db():
    """Drop all tables"""
    if click.confirm('Are you sure you want to drop all tables?'):
        click.echo('Dropping database...')
        db.drop_all()
        click.echo('Database dropped.')

@cli.command('reset-db')
def reset_db():
    """Reset database (drop and recreate)"""
    if click.confirm('Are you sure you want to reset the database?'):
        click.echo('Resetting database...')
        db.drop_all()
        db.create_all()
        click.echo('Database reset.')

@cli.command('seed')
@click.option('--sample-data', is_flag=True, help='Include sample data')
def seed(sample_data):
    """Seed database with initial data"""
    click.echo('Seeding database...')
    
    # Create system settings
    if not SystemSettings.query.get(1):
        click.echo('Creating default system settings...')
        settings = SystemSettings()
        db.session.add(settings)
        db.session.commit()

    # Create default niches
    if sample_data:
        click.echo('Creating sample niches...')
        default_niches = [
            ('Fitness', 20),
            ('Fashion', 15),
            ('Food', 10),
            ('Travel', 12),
            ('Lifestyle', 18)
        ]
        
        for name, target in default_niches:
            if not Niche.query.filter_by(name=name).first():
                niche = Niche(name=name, daily_story_target=target)
                db.session.add(niche)
                db.session.commit()
                click.echo(f'Created niche: {name}')

    click.echo('Database seeded.')

@cli.command('status')
def status():
    """Show database status"""
    click.echo('Database Status:')
    
    # Check connection
    try:
        db.session.execute('SELECT 1')
        click.echo('Connection: OK')
    except Exception as e:
        click.echo(f'Connection: ERROR - {str(e)}')
        return

    # Show table counts
    from models import Profile, Batch, StoryResult, Proxy
    
    click.echo('\nRecord Counts:')
    click.echo(f'Profiles: {Profile.query.count()}')
    click.echo(f'Niches: {Niche.query.count()}')
    click.echo(f'Active Batches: {Batch.query.filter_by(status="running").count()}')
    click.echo(f'Active Stories: {StoryResult.query.filter_by(is_expired=False).count()}')
    click.echo(f'Active Proxies: {Proxy.query.filter_by(is_active=True).count()}')

if __name__ == '__main__':
    cli()
