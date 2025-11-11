# CreativeScript LMS - Development Journey

## 🚨 Challenges Faced & Solutions

### 1. **Admin User Bootstrap - Chicken & Egg Problem**
**Challenge:** How to create the first admin user when the API only allows regular user registration?

**Root Cause:**
- Register endpoint always created REGULAR role users
- No way to set role during registration
- Admin must exist to create other admins

**Solution - Created CLI Tool:**
```python
# src/cli.py
# Reads from environment variables or interactive input
# Creates admin user directly in database
```
```bash
# boot/docker-run.sh
# Runs CLI before starting app if env vars are set
if [ -n "$ADMIN_USERNAME" ]; then
    python src/cli.py
fi
```

Benefits:
- No hardcoded credentials
- Works with environment variables
- Falls back to interactive mode
- Runs automatically in Docker

---

### 2. **User Permission Constraints - Removing vs Rejecting**
**Challenge:** Non-admin users were getting rejected when trying to update `is_active` or `role` fields, but they should just ignore those fields.

**Initial Approach:** Return 400 error if restricted fields provided
```python
if current_user.role != UserRole.ADMIN and "is_active" in update_data:
    raise HTTPException(400, "Cannot modify is_active")
```

**Problem:** API was too strict, rejected valid partial updates

**Solution: Silently Ignore Restricted Fields**
```python
# Extract update data
update_data = user_update.model_dump(exclude_unset=True)

# For non-admins, remove restricted fields
if current_user.role != UserRole.ADMIN:
    update_data.pop("is_active", None)
    update_data.pop("role", None)

# Apply allowed updates only
for field, value in update_data.items():
    setattr(user, field, value)
```

Benefits:
- Better UX (doesn't reject the entire request)
- Admins still get full control
- Clean API behavior

---

### 3. **Copy Management - Database Design**
**Challenge:** How to store multiple physical copies of the same book efficiently?

**Initial Approach:** Store `total_copies` and `available_copies` in Book table
- **Problem:** sync issues, complex update logic

**Second Approach:** One row per physical copy
- **Problem:** Seemed wasteful to repeat book data

**Final Solution: One Row Per Copy + On-Demand Calculation**
```sql
-- Count total copies (same ISBN)
SELECT COUNT(*) FROM book WHERE isbn = '978-0-xxx'

-- Count available copies (subtract borrowed)
SELECT COUNT(*) FROM book 
WHERE isbn = '978-0-xxx' 
AND id NOT IN (
    SELECT book_id FROM transaction 
    WHERE is_returned = false
)
```

Benefits:
- ✅ Single source of truth (transactions)
- ✅ No sync issues
- ✅ Always accurate
- ✅ Can track specific damaged books

---

### 4. **Availability Validation on Borrow**
**Challenge:** Users could borrow books even when no copies were available.

**Root Cause:** No validation in `create_transaction`

**Solution:** Added availability check
```python
def create_transaction(db: Session, transaction_data: TransactionCreate):
    available = calculate_available_copies(db, transaction_data.book_id)
    if available <= 0:
        raise ValueError("No available copies of this book to borrow")
```

---

### 5. **Privacy - Book Borrowing History**
**Challenge:** Any user could view who borrowed which books (privacy issue).

**Solution:** Made `/book/{book_id}` borrowing history **admin-only**
```python
@router.get("/book/{book_id}")
async def get_book_transactions_endpoint(
    book_id: int,
    current_user = Depends(require_admin)  # Admin only!
):
    ...
```

Benefits:
- Protects user privacy
- Prevents tracking which books specific users borrowed
---

## 💡 What I Would Do Differently (With More Time)

### 1. **Database Triggers for Copy Counts**
Instead of calculating on-demand, use PostgreSQL triggers:
```sql
CREATE TRIGGER update_available_copies
AFTER INSERT/UPDATE ON transaction
FOR EACH ROW
EXECUTE FUNCTION update_book_availability();
```
- Faster read performance
- Still maintains accuracy
- No duplicate data

### 2. **Separate Copy Entity**
For larger systems, separate Book and BookCopy:
```
Book: {id, title, isbn, author_id}
BookCopy: {id, book_id, condition, location, acquisition_date}
Transaction: references BookCopy, not Book
```
Benefits:
- Track individual copy condition/location
- No data redundancy
- Better for physical library management

### 3. **Logging**

### 4. **Rate Limiting & Caching**

---

## 📚 What I Learned

### 1. **Database Design Impacts Everything**

### 2. **Docker Makes Deployment Easy**

### 3. **Variable naming and comments helps when codebase grows**
---


