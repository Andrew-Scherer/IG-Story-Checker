# Profile Import Investigation Plan

## Core Issues:
1. Detecting duplicate profiles is too sensitive
2. Profiles may be in the database but not listed in the UI
3. Difficulty importing thousands of profiles at once

## Investigation Plan

### 1. Duplicate Profile Detection

#### 1.1 Analyze current duplicate detection logic
- [ ] Review duplicate check in `server/api/profile.py` (import_profiles function)
- [ ] Identify the exact criteria used for flagging duplicates

#### 1.2 Test duplicate detection sensitivity
- [ ] Create a test dataset with known duplicates and slight variations
- [ ] Implement logging for duplicate detection process
- [ ] Run import process with test dataset and analyze results
- [ ] Quantify false positive rate for duplicate detection

### 2. Database vs UI Discrepancy

#### 2.1 Verify database content
- [ ] Implement a database query to count total profiles
- [ ] Create a query to list recently added profiles

#### 2.2 Analyze UI listing logic
- [ ] Review profile fetching in `client/src/stores/profileStore.js`
- [ ] Examine any filtering or pagination logic that might affect profile listing

#### 2.3 Compare database to UI
- [ ] Implement a test that adds known profiles to the database
- [ ] Verify these profiles appear correctly in the UI
- [ ] Identify any discrepancies between database content and UI display

### 3. Large-Scale Import Performance

#### 3.1 Profile current import process
- [ ] Implement performance logging in the import process
- [ ] Test import with varying numbers of profiles (e.g., 100, 1000, 10000)
- [ ] Identify performance bottlenecks

#### 3.2 Analyze database operations
- [ ] Review database queries during import process
- [ ] Identify any inefficient queries or lack of batch operations

#### 3.3 Memory usage analysis
- [ ] Monitor server memory usage during large imports
- [ ] Identify any memory leaks or excessive memory usage

## Testing Plan

### 1. Duplicate Detection Testing
- [ ] Create a script to generate test profiles with controlled levels of similarity
- [ ] Run import tests with these profiles and measure false positive/negative rates
- [ ] Adjust duplicate detection criteria based on test results

### 2. UI-Database Consistency Testing
- [ ] Develop an automated test that adds profiles to the database and verifies UI display
- [ ] Test various scenarios: different niches, statuses, and large numbers of profiles

### 3. Large-Scale Import Testing
- [ ] Create datasets of varying sizes (1K, 10K, 100K profiles)
- [ ] Implement automated performance tests for imports
- [ ] Measure time, CPU usage, and memory consumption for each test

## Next Steps
After completing the investigation and testing, we will:
1. Analyze results and identify root causes of each issue
2. Develop specific solutions for each problem area
3. Implement and test fixes iteratively
4. Re-run performance and accuracy tests to verify improvements