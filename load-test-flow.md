## Lead creation part: ...

## Frontend load test:

Testing the frontend based on the basic flow. Works in following stages / task types.

### Task 1: Initial Login

When logging in, many APIs are called. (Subtasks 3-11 are called parallelly)

1. Login api - `login`
2. User info - `users/my_info`
3. All boxes - `box/get_all_box/{sub_org_id}`
4. Organization users - `organization/sub_organizations/{sub_org_id}/organization_users`
5. Channels:
   - All global channels - `channels/get_all_global_channels`
   - All pending channels - `channels/{sub_org_id}/get_all_pending_channels`
   - All connected channels - `channels/{sub_org_id}/get_all_connected_channels`
6. Get or create nudges - `organization/get_or_create_nudges`
7. Get Reply templates - `reply_templates/sub_organizations/{sub_org_id}/templates/`
8. Get plans - `plans/get_plans/{sub_org_id}`
9. Get countries - `countries/get_countries_list`
10. Get lead counts:
    - `leads/get_all_lead_count`
    - `leads/sub_organizations/{sub_org_id}/things_to_do/get_the_count_enquiry_and_task`
11. Things to do list

### Task 2: Things to do

User checks the leads in things to do.

### Task 3: View Box Leads

User clicks on box, causing all the stages leads to load.

### Task 4: Load stage leads

User scrolls on a particular stage, causing more leads to load.
