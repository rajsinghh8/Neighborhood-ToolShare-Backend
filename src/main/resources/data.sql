INSERT INTO users (id, name, email, password, neighborhood, phone, api_key, created_at, updated_at)
VALUES
    (1, 'Alice Johnson', 'alice@example.com', '$2b$12$qVviiDYu6NHf26YzlnhK6.CPY7sxIMOKLcqbWfvJX9cdoIDHxC9Gi', 'Maple Heights', '555-0100', 'seed-api-key-alice-0000000000001', now(), now()),
    (2, 'Bob Smith', 'bob@example.com', '$2b$12$qVviiDYu6NHf26YzlnhK6.CPY7sxIMOKLcqbWfvJX9cdoIDHxC9Gi', 'Maple Heights', '555-0101', 'seed-api-key-bob-00000000000002', now(), now()),
    (3, 'Carol Davis', 'carol@example.com', '$2b$12$qVviiDYu6NHf26YzlnhK6.CPY7sxIMOKLcqbWfvJX9cdoIDHxC9Gi', 'Riverside', '555-0102', 'seed-api-key-carol-0000000000003', now(), now()),
    (4, 'David Lee', 'david@example.com', '$2b$12$qVviiDYu6NHf26YzlnhK6.CPY7sxIMOKLcqbWfvJX9cdoIDHxC9Gi', 'Riverside', '555-0103', 'seed-api-key-david-0000000000004', now(), now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));

INSERT INTO tools (id, name, category, description, condition, owner_id, available, created_at, updated_at)
VALUES
    (1, 'Cordless Drill', 'Power Tools', 'An 18V cordless drill with two batteries', 'GOOD', 1, true, now(), now()),
    (2, 'Lawn Mower', 'Gardening', 'Push lawn mower, well maintained', 'GOOD', 1, true, now(), now()),
    (3, 'Pressure Washer', 'Cleaning', 'Electric pressure washer, 1800 PSI', 'FAIR', 2, true, now(), now()),
    (4, 'Hedge Trimmer', 'Gardening', 'Corded hedge trimmer', 'NEW', 3, true, now(), now()),
    (5, 'Ladder', 'Power Tools', '6 foot aluminum step ladder', 'GOOD', 4, true, now(), now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('tools_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tools));

INSERT INTO borrow_requests (id, tool_id, borrower_id, requested_start_date, requested_end_date, status, created_at, updated_at)
VALUES
    (1, 3, 1, CURRENT_DATE, CURRENT_DATE + INTERVAL '3 day', 'PENDING', now(), now()),
    (2, 4, 2, CURRENT_DATE - INTERVAL '5 day', CURRENT_DATE - INTERVAL '2 day', 'RETURNED', now(), now()),
    (3, 1, 3, CURRENT_DATE - INTERVAL '10 day', CURRENT_DATE - INTERVAL '7 day', 'RETURNED', now(), now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('borrow_requests_id_seq', (SELECT COALESCE(MAX(id), 1) FROM borrow_requests));

INSERT INTO reservations (id, borrow_request_id, start_date, end_date, pickup_notes, return_notes, created_at, updated_at)
VALUES
    (1, 2, CURRENT_DATE - INTERVAL '5 day', CURRENT_DATE - INTERVAL '2 day', 'Picked up from front porch', 'Returned clean', now(), now()),
    (2, 3, CURRENT_DATE - INTERVAL '10 day', CURRENT_DATE - INTERVAL '7 day', 'Picked up at garage', 'Returned on time', now(), now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('reservations_id_seq', (SELECT COALESCE(MAX(id), 1) FROM reservations));

INSERT INTO reviews (id, reservation_id, reviewer_id, reviewee_id, rating, comment, created_at)
VALUES
    (1, 1, 2, 3, 5, 'Great tool, exactly as described.', now()),
    (2, 1, 3, 2, 5, 'Responsible borrower, returned on time.', now()),
    (3, 2, 3, 1, 4, 'Good drill, worked well.', now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('reviews_id_seq', (SELECT COALESCE(MAX(id), 1) FROM reviews));

INSERT INTO notifications (id, user_id, message, type, read, created_at)
VALUES
    (1, 1, 'New borrow request for your tool ''Pressure Washer'' from Alice Johnson', 'NEW_REQUEST', false, now()),
    (2, 2, 'Your tool ''Hedge Trimmer'' was returned', 'RETURNED', true, now()),
    (3, 3, 'Your request for ''Cordless Drill'' was approved', 'APPROVED', true, now())
ON CONFLICT (id) DO NOTHING;

SELECT setval('notifications_id_seq', (SELECT COALESCE(MAX(id), 1) FROM notifications));
