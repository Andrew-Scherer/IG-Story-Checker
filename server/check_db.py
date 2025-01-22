from app import create_app
from models import db, Profile, Niche, Batch, BatchProfile
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("\n=== Checking Database ===")
    
    try:
        # Test database connection
        print("\nTesting database connection...")
        result = db.session.execute(text('SELECT 1')).scalar()
        print(f"Database connection test: {result == 1}")
        
        print("\nNiches:")
        niches = Niche.query.all()
        if niches:
            for n in niches:
                print(f"ID: {n.id}, Name: {n.name}")
                # Get profiles in this niche
                niche_profiles = Profile.query.filter_by(niche_id=n.id).all()
                print(f"  Profiles in niche: {len(niche_profiles)}")
                for p in niche_profiles:
                    print(f"    - {p.username} (ID: {p.id})")
        else:
            print("No niches found")
        
        print("\nProfiles without niche:")
        no_niche_profiles = Profile.query.filter_by(niche_id=None).all()
        for p in no_niche_profiles:
            print(f"- {p.username} (ID: {p.id})")
        
        print("\nBatches:")
        batches = Batch.query.all()
        if batches:
            for b in batches:
                print(f"\nBatch {b.id}:")
                print(f"  Status: {b.status}")
                print(f"  Queue Position: {b.queue_position}")
                print(f"  Niche ID: {b.niche_id}")
                print(f"  Total Profiles: {b.total_profiles}")
                print(f"  Completed: {b.completed_profiles}")
                print(f"  Successful: {b.successful_checks}")
                print(f"  Failed: {b.failed_checks}")
                print("\n  Batch Profiles:")
                for bp in b.profiles:
                    print(f"    - Profile ID: {bp.profile_id}")
                    print(f"      Status: {bp.status}")
                    print(f"      Has Story: {bp.has_story}")
                    print(f"      Error: {bp.error}")
                    print(f"      Processed At: {bp.processed_at}")
        else:
            print("No batches found")
            
        print("\nBatch Profiles:")
        batch_profiles = BatchProfile.query.all()
        if batch_profiles:
            print(f"Found {len(batch_profiles)} batch profiles")
            for bp in batch_profiles:
                print(f"\nBatch Profile:")
                print(f"  ID: {bp.id}")
                print(f"  Batch ID: {bp.batch_id}")
                print(f"  Profile ID: {bp.profile_id}")
                print(f"  Status: {bp.status}")
                print(f"  Has Story: {bp.has_story}")
                print(f"  Error: {bp.error}")
                print(f"  Processed At: {bp.processed_at}")
        else:
            print("No batch profiles found")
            
        # Test batch creation
        print("\nTesting batch creation...")
        test_niche_id = "5fa11468-964e-44e7-b2da-acb464670d07"  # The niche ID we found
        test_profile_ids = ["9ddcc7c5-cdf0-4f58-8949-6f7572e4cd36", "13d277fa-e6d3-41d5-8aef-ab1df3fdc121"]  # Two profile IDs from that niche
        
        print(f"Creating test batch with niche_id: {test_niche_id}")
        print(f"Profile IDs: {test_profile_ids}")
        
        # Verify profiles exist
        profiles = Profile.query.filter(Profile.id.in_(test_profile_ids)).all()
        print(f"Found {len(profiles)} matching profiles")
        for p in profiles:
            print(f"  - {p.username} (ID: {p.id})")
            print(f"    Niche ID: {p.niche_id}")
            
        # Create test batch
        try:
