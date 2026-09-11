#!/bin/bash
# Full lifecycle test for Neighborhood ToolShare Backend
# Covers: auth, users, tools, borrow-requests, reservations, reviews, notifications, admin

BASE_URL="http://localhost:25084"
RESULTS_FILE="/tmp/test_results.log"
> "$RESULTS_FILE"

PASS_COUNT=0
FAIL_COUNT=0

record() {
  local name="$1" code="$2" expected="$3" extra="$4"
  if [ "$code" = "$expected" ]; then
    echo "PASS|$name|$code|$extra" >> "$RESULTS_FILE"
    PASS_COUNT=$((PASS_COUNT+1))
  else
    echo "FAIL|$name|$code (expected $expected)|$extra" >> "$RESULTS_FILE"
    FAIL_COUNT=$((FAIL_COUNT+1))
  fi
}

RAND=$RANDOM
OWNER_EMAIL="owner_${RAND}@example.com"
BORROWER_EMAIL="borrower_${RAND}@example.com"
PASSWORD="Secret123"

echo "== Register owner =="
REG_OWNER=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Owner User\",\"email\":\"$OWNER_EMAIL\",\"password\":\"$PASSWORD\",\"neighborhood\":\"Maple Heights\",\"phone\":\"555-1111\"}")
OWNER_CODE=$(echo "$REG_OWNER" | tail -1)
OWNER_BODY=$(echo "$REG_OWNER" | sed '$d')
OWNER_TOKEN=$(echo "$OWNER_BODY" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
record "POST /auth/register (owner)" "$OWNER_CODE" "201" "$OWNER_BODY"

echo "== Register borrower =="
REG_BORROWER=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Borrower User\",\"email\":\"$BORROWER_EMAIL\",\"password\":\"$PASSWORD\",\"neighborhood\":\"Maple Heights\",\"phone\":\"555-2222\"}")
BORROWER_CODE=$(echo "$REG_BORROWER" | tail -1)
BORROWER_BODY=$(echo "$REG_BORROWER" | sed '$d')
BORROWER_TOKEN=$(echo "$BORROWER_BODY" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
BORROWER_ID=$(echo "$BORROWER_BODY" | grep -o '"userId":[0-9]*' | head -1 | cut -d':' -f2)
record "POST /auth/register (borrower)" "$BORROWER_CODE" "201" "$BORROWER_BODY"

echo "== Register duplicate email (expect 400/409) =="
DUP=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Dup\",\"email\":\"$OWNER_EMAIL\",\"password\":\"$PASSWORD\"}")
if [ "$DUP" = "400" ] || [ "$DUP" = "409" ]; then
  record "POST /auth/register (duplicate - reject)" "$DUP" "$DUP" "correctly rejected"
else
  record "POST /auth/register (duplicate - reject)" "$DUP" "400" "expected rejection"
fi

echo "== Login owner =="
LOGIN=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$OWNER_EMAIL\",\"password\":\"$PASSWORD\"}")
LOGIN_CODE=$(echo "$LOGIN" | tail -1)
LOGIN_BODY=$(echo "$LOGIN" | sed '$d')
record "POST /auth/login (owner)" "$LOGIN_CODE" "200" "$LOGIN_BODY"

echo "== Login wrong password (expect 401) =="
BADLOGIN=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$OWNER_EMAIL\",\"password\":\"wrongpass\"}")
record "POST /auth/login (wrong password - reject)" "$BADLOGIN" "401" "expected rejection"

echo "== GET /users/me (owner) =="
ME=$(curl -s --max-time 60 -w "\n%{http_code}" "$BASE_URL/api/v1/users/me" -H "Authorization: Bearer $OWNER_TOKEN")
ME_CODE=$(echo "$ME" | tail -1)
record "GET /users/me (owner)" "$ME_CODE" "200" ""

echo "== GET /users/me no token (expect 401/403) =="
NOAUTH=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/users/me")
if [ "$NOAUTH" = "401" ] || [ "$NOAUTH" = "403" ]; then
  record "GET /users/me (no auth - reject)" "$NOAUTH" "$NOAUTH" "correctly rejected"
else
  record "GET /users/me (no auth - reject)" "$NOAUTH" "401" "expected rejection"
fi

echo "== PUT /users/me =="
UPDATEME=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/users/me" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Owner Updated","neighborhood":"Oak Grove","phone":"555-9999"}')
record "PUT /users/me" "$UPDATEME" "200" ""

echo "== POST /tools (owner creates tool) =="
TOOL=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/tools" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Circular Saw","category":"Power Tools","description":"7 1/4 inch","condition":"GOOD","available":true}')
TOOL_CODE=$(echo "$TOOL" | tail -1)
TOOL_BODY=$(echo "$TOOL" | sed '$d')
TOOL_ID=$(echo "$TOOL_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "POST /tools" "$TOOL_CODE" "201" "$TOOL_BODY"

echo "== GET /tools (search, paginated) =="
SEARCH=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/tools?category=Power%20Tools&available=true" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /tools (search)" "$SEARCH" "200" ""

echo "== GET /tools/mine (owner) =="
MINE=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/tools/mine" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "GET /tools/mine" "$MINE" "200" ""

echo "== GET /tools/{id} =="
GETTOOL=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/tools/$TOOL_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /tools/{id}" "$GETTOOL" "200" ""

echo "== PUT /tools/{id} (owner edits) =="
EDITTOOL=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/tools/$TOOL_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Circular Saw Pro","category":"Power Tools","description":"7 1/4 inch, updated","condition":"GOOD","available":true}')
record "PUT /tools/{id}" "$EDITTOOL" "200" ""

echo "== PUT /tools/{id} (non-owner edits - expect 403) =="
EDITFORBIDDEN=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/tools/$TOOL_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Hacked","category":"Power Tools","description":"x","condition":"GOOD","available":true}')
record "PUT /tools/{id} (non-owner - reject)" "$EDITFORBIDDEN" "403" "expected rejection"

echo "== POST /borrow-requests (own tool - expect 400) =="
OWNBORROW=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/borrow-requests" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"toolId\":$TOOL_ID,\"requestedStartDate\":\"2025-01-01\",\"requestedEndDate\":\"2025-01-05\"}")
record "POST /borrow-requests (own tool - reject)" "$OWNBORROW" "400" "expected rejection"

TODAY=$(date +%F)
END_DATE=$(date -d "+3 days" +%F 2>/dev/null || date -v+3d +%F)

echo "== POST /borrow-requests (borrower requests tool) =="
BR=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/borrow-requests" \
  -H "Authorization: Bearer $BORROWER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"toolId\":$TOOL_ID,\"requestedStartDate\":\"$TODAY\",\"requestedEndDate\":\"$END_DATE\"}")
BR_CODE=$(echo "$BR" | tail -1)
BR_BODY=$(echo "$BR" | sed '$d')
BR_ID=$(echo "$BR_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "POST /borrow-requests" "$BR_CODE" "201" "$BR_BODY"

echo "== GET /borrow-requests?role=borrower =="
BRLIST=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/borrow-requests?role=borrower" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /borrow-requests?role=borrower" "$BRLIST" "200" ""

echo "== GET /borrow-requests?role=owner =="
BRLISTOWNER=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/borrow-requests?role=owner" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "GET /borrow-requests?role=owner" "$BRLISTOWNER" "200" ""

echo "== GET /borrow-requests/{id} =="
BRGET=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/borrow-requests/$BR_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /borrow-requests/{id}" "$BRGET" "200" ""

echo "== POST another borrow-request on unavailable tool after approve will be tested later =="

echo "== PUT /borrow-requests/{id}/approve (non-owner - expect 403) =="
APPROVEFORBIDDEN=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/borrow-requests/$BR_ID/approve" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "PUT /borrow-requests/{id}/approve (non-owner - reject)" "$APPROVEFORBIDDEN" "403" "expected rejection"

echo "== PUT /borrow-requests/{id}/approve (owner approves) =="
APPROVE=$(curl -s --max-time 60 -w "\n%{http_code}" -X PUT "$BASE_URL/api/v1/borrow-requests/$BR_ID/approve" \
  -H "Authorization: Bearer $OWNER_TOKEN")
APPROVE_CODE=$(echo "$APPROVE" | tail -1)
record "PUT /borrow-requests/{id}/approve" "$APPROVE_CODE" "200" ""

echo "== Verify tool now unavailable =="
GETTOOL2=$(curl -s --max-time 60 "$BASE_URL/api/v1/tools/$TOOL_ID" -H "Authorization: Bearer $BORROWER_TOKEN")
AVAILABLE=$(echo "$GETTOOL2" | grep -o '"available":[a-z]*' | cut -d':' -f2)
if [ "$AVAILABLE" = "false" ]; then
  record "Tool availability rule (unavailable after approve)" "false" "false" "correct"
else
  record "Tool availability rule (unavailable after approve)" "$AVAILABLE" "false" "incorrect"
fi

echo "== GET /reservations?role=borrower =="
RESLIST=$(curl -s --max-time 60 -w "\n%{http_code}" "$BASE_URL/api/v1/reservations?role=borrower" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
RESLIST_CODE=$(echo "$RESLIST" | tail -1)
RESLIST_BODY=$(echo "$RESLIST" | sed '$d')
RES_ID=$(echo "$RESLIST_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "GET /reservations?role=borrower" "$RESLIST_CODE" "200" "$RESLIST_BODY"

echo "== GET /reservations/{id} =="
RESGET=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/reservations/$RES_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /reservations/{id}" "$RESGET" "200" ""

echo "== PUT /reservations/{id} (update notes) =="
RESUPDATE=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/reservations/$RES_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN" -H "Content-Type: application/json" \
  -d '{"pickupNotes":"Picked up at 10am","returnNotes":""}')
record "PUT /reservations/{id}" "$RESUPDATE" "200" ""

echo "== PUT /borrow-requests/{id}/activate =="
ACTIVATE=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/borrow-requests/$BR_ID/activate" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "PUT /borrow-requests/{id}/activate" "$ACTIVATE" "200" ""

echo "== PUT /borrow-requests/{id}/return =="
RETURN=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/borrow-requests/$BR_ID/return" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "PUT /borrow-requests/{id}/return" "$RETURN" "200" ""

echo "== Verify tool available again after return =="
GETTOOL3=$(curl -s --max-time 60 "$BASE_URL/api/v1/tools/$TOOL_ID" -H "Authorization: Bearer $BORROWER_TOKEN")
AVAILABLE2=$(echo "$GETTOOL3" | grep -o '"available":[a-z]*' | cut -d':' -f2)
if [ "$AVAILABLE2" = "true" ]; then
  record "Tool availability rule (available after return)" "true" "true" "correct"
else
  record "Tool availability rule (available after return)" "$AVAILABLE2" "true" "incorrect"
fi

echo "== POST /reviews (borrower reviews owner) =="
OWNER_ID=$(echo "$OWNER_BODY" | grep -o '"userId":[0-9]*' | head -1 | cut -d':' -f2)
REVIEW=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/reviews" \
  -H "Authorization: Bearer $BORROWER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"reservationId\":$RES_ID,\"revieweeId\":$OWNER_ID,\"rating\":5,\"comment\":\"Great tool and owner!\"}")
REVIEW_CODE=$(echo "$REVIEW" | tail -1)
REVIEW_BODY=$(echo "$REVIEW" | sed '$d')
REVIEW_ID=$(echo "$REVIEW_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "POST /reviews (borrower->owner)" "$REVIEW_CODE" "201" "$REVIEW_BODY"

echo "== POST /reviews (owner reviews borrower - two-way) =="
REVIEW2=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/reviews" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"reservationId\":$RES_ID,\"revieweeId\":$BORROWER_ID,\"rating\":4,\"comment\":\"Returned on time.\"}")
REVIEW2_CODE=$(echo "$REVIEW2" | tail -1)
record "POST /reviews (owner->borrower, two-way)" "$REVIEW2_CODE" "201" ""

echo "== POST /reviews duplicate (expect 400) =="
REVIEWDUP=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/reviews" \
  -H "Authorization: Bearer $BORROWER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"reservationId\":$RES_ID,\"revieweeId\":$OWNER_ID,\"rating\":3,\"comment\":\"dup\"}")
record "POST /reviews (duplicate - reject)" "$REVIEWDUP" "400" "expected rejection"

echo "== GET /reviews/user/{userId} =="
REVIEWSFORUSER=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/reviews/user/$OWNER_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /reviews/user/{userId}" "$REVIEWSFORUSER" "200" ""

echo "== GET /reviews/{id} =="
REVIEWGET=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "GET /reviews/{id}" "$REVIEWGET" "200" ""

echo "== GET /notifications (owner) =="
NOTIF=$(curl -s --max-time 60 -w "\n%{http_code}" "$BASE_URL/api/v1/notifications" \
  -H "Authorization: Bearer $OWNER_TOKEN")
NOTIF_CODE=$(echo "$NOTIF" | tail -1)
NOTIF_BODY=$(echo "$NOTIF" | sed '$d')
NOTIF_ID=$(echo "$NOTIF_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "GET /notifications" "$NOTIF_CODE" "200" "$NOTIF_BODY"

echo "== PUT /notifications/{id}/read =="
if [ -n "$NOTIF_ID" ]; then
  NOTIFREAD=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/notifications/$NOTIF_ID/read" \
    -H "Authorization: Bearer $OWNER_TOKEN")
  record "PUT /notifications/{id}/read" "$NOTIFREAD" "200" ""
else
  record "PUT /notifications/{id}/read" "SKIPPED" "200" "no notification id found"
fi

echo "== GET /admin/overdue-users =="
OVERDUE=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/overdue-users?minCount=1" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "GET /admin/overdue-users" "$OVERDUE" "200" ""

echo "== GET /admin/flagged-tools =="
FLAGGED=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/flagged-tools?minCount=1" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "GET /admin/flagged-tools" "$FLAGGED" "200" ""

echo "== DELETE /tools/{id} (non-owner - expect 403) =="
DELFORBIDDEN=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/tools/$TOOL_ID" \
  -H "Authorization: Bearer $BORROWER_TOKEN")
record "DELETE /tools/{id} (non-owner - reject)" "$DELFORBIDDEN" "403" "expected rejection"

echo "== DELETE /tools/{id} (owner, tool has borrow history - expect 400 by design) =="
DELHISTORY=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/tools/$TOOL_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "DELETE /tools/{id} (has borrow history - reject by design)" "$DELHISTORY" "400" "existing borrow request history blocks deletion"

echo "== Mark tool unavailable instead (owner) - alternative to delete =="
MARKUNAVAIL=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/api/v1/tools/$TOOL_ID/availability?available=false" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "PUT /tools/{id}/availability" "$MARKUNAVAIL" "200" ""

echo "== POST /tools (fresh tool with no history, for delete-success case) =="
FRESHTOOL=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/tools" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Ladder","category":"Misc","description":"6ft ladder","condition":"NEW","available":true}')
FRESHTOOL_CODE=$(echo "$FRESHTOOL" | tail -1)
FRESHTOOL_BODY=$(echo "$FRESHTOOL" | sed '$d')
FRESHTOOL_ID=$(echo "$FRESHTOOL_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
record "POST /tools (fresh, for delete test)" "$FRESHTOOL_CODE" "201" ""

echo "== DELETE /tools/{id} (owner, no history - expect 204) =="
DEL=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/tools/$FRESHTOOL_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "DELETE /tools/{id} (no history)" "$DEL" "204" ""

echo "== GET /tools/{id} after delete (expect 404) =="
GETDELETED=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/tools/$FRESHTOOL_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN")
record "GET /tools/{id} after delete (404 confirm)" "$GETDELETED" "404" "expected 404"

echo "== GET /actuator/health =="
HEALTH=$(curl -s --max-time 60 -o /dev/null -w "%{http_code}" "$BASE_URL/actuator/health")
record "GET /actuator/health" "$HEALTH" "200" ""

echo ""
echo "===================== RESULTS ====================="
cat "$RESULTS_FILE"
echo "====================================================="
echo "PASSED: $PASS_COUNT  FAILED: $FAIL_COUNT"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "PASSED"
  exit 0
else
  echo "FAILED: $FAIL_COUNT test(s) failed"
  exit 1
fi
