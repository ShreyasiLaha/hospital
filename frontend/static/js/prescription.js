/**
 * CarePlus Hospital - Prescription Builder Dynamic Script
 * Handles dynamically adding and removing medication input rows in the doctor portal.
 */

document.addEventListener('DOMContentLoaded', function () {
    const addMedicineBtn = document.getElementById('add_medicine_row');
    const medicineTableBody = document.getElementById('medicine_items_tbody');

    if (addMedicineBtn && medicineTableBody) {
        addMedicineBtn.addEventListener('click', function () {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <input type="text" class="form-control form-control-sm" name="medicine_name[]" placeholder="e.g. Paracetamol" required>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm" name="dosage[]" placeholder="650 mg" required>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm" name="frequency[]" placeholder="1-0-1 (After food)" required>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm" name="duration[]" placeholder="3 Days" required>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm" name="instructions[]" placeholder="Take with warm water">
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-sm btn-outline-danger remove-medicine-row">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;

            // Attach remove listener
            tr.querySelector('.remove-medicine-row').addEventListener('click', function () {
                if (medicineTableBody.querySelectorAll('tr').length > 1) {
                    tr.remove();
                } else {
                    alert('Prescription must contain at least one medication item.');
                }
            });

            medicineTableBody.appendChild(tr);
        });

        // Attach remove listener to existing rows
        document.querySelectorAll('.remove-medicine-row').forEach(btn => {
            btn.addEventListener('click', function () {
                const tr = this.closest('tr');
                if (medicineTableBody.querySelectorAll('tr').length > 1) {
                    tr.remove();
                } else {
                    alert('Prescription must contain at least one medication item.');
                }
            });
        });
    }
});
