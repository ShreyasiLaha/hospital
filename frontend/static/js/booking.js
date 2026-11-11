/**
 * CarePlus Hospital - Dynamic Appointment Booking Client Script
 * Handles real-time department doctor lookup and available slot calculation.
 */

document.addEventListener('DOMContentLoaded', function () {
    const departmentSelect = document.getElementById('department_select');
    const doctorSelect = document.getElementById('doctor_select');
    const appointmentDate = document.getElementById('appointment_date');
    const slotContainer = document.getElementById('slot_container');
    const selectedSlotInput = document.getElementById('selected_slot_time');
    const doctorInfoBox = document.getElementById('doctor_info_box');
    const submitBtn = document.getElementById('submit_booking_btn');

    // Restrict date picker to today or future dates (using local timezone)
    if (appointmentDate) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        appointmentDate.setAttribute('min', `${year}-${month}-${day}`);
    }

    // Form submit check: ensure a slot was chosen
    const appointmentForm = document.getElementById('appointment_form');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', function (e) {
            if (!selectedSlotInput || !selectedSlotInput.value) {
                e.preventDefault();
                alert('Please select an available consultation time slot.');
            }
        });
    }

    // 1. Department Change: Fetch doctors
    if (departmentSelect && doctorSelect) {
        departmentSelect.addEventListener('change', function () {
            const deptId = this.value;
            doctorSelect.innerHTML = '<option value="">Loading specialists...</option>';
            doctorSelect.disabled = true;
            if (slotContainer) {
                slotContainer.innerHTML = '<span class="text-muted small">Please select doctor and date to view time slots.</span>';
            }
            if (selectedSlotInput) selectedSlotInput.value = '';
            if (doctorInfoBox) doctorInfoBox.classList.add('d-none');
            if (submitBtn) submitBtn.disabled = true;

            if (!deptId) {
                doctorSelect.innerHTML = '<option value="">-- Choose department first --</option>';
                return;
            }

            fetch(`/api/doctors-by-department/${deptId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' && data.doctors && data.doctors.length > 0) {
                        doctorSelect.innerHTML = '<option value="">-- Choose Specialist Doctor --</option>';
                        data.doctors.forEach(doc => {
                            const opt = document.createElement('option');
                            opt.value = doc.id;
                            const fee = typeof doc.fee === 'number' ? doc.fee : parseFloat(doc.fee || 0);
                            opt.textContent = `${doc.name} (${doc.specialization}) - Fee: $${fee.toFixed(2)}`;
                            opt.dataset.fee = fee;
                            opt.dataset.room = doc.room || 'General OPD';
                            opt.dataset.exp = doc.experience || 0;
                            opt.dataset.qual = doc.qualification || '';
                            doctorSelect.appendChild(opt);
                        });
                        doctorSelect.disabled = false;
                    } else {
                        doctorSelect.innerHTML = '<option value="">No active doctors in this department</option>';
                        doctorSelect.disabled = true;
                    }
                })
                .catch(err => {
                    console.error('Error fetching doctors:', err);
                    doctorSelect.innerHTML = '<option value="">Error loading doctors</option>';
                    doctorSelect.disabled = true;
                });
        });
    }

    // 2. Doctor selection change
    if (doctorSelect) {
        doctorSelect.addEventListener('change', function () {
            const opt = this.options[this.selectedIndex];
            if (opt && opt.value && doctorInfoBox) {
                const roomEl = document.getElementById('info_room');
                const feeEl = document.getElementById('info_fee');
                const expEl = document.getElementById('info_exp');
                if (roomEl) roomEl.textContent = opt.dataset.room || 'General OPD';
                if (feeEl) feeEl.textContent = `$${parseFloat(opt.dataset.fee || 0).toFixed(2)}`;
                if (expEl) expEl.textContent = `${opt.dataset.exp || 0} Years Experience`;
                doctorInfoBox.classList.remove('d-none');
            } else if (doctorInfoBox) {
                doctorInfoBox.classList.add('d-none');
            }
            fetchSlots();
        });
    }

    // 3. Date selection change
    if (appointmentDate) {
        appointmentDate.addEventListener('change', fetchSlots);
    }

    function fetchSlots() {
        if (!doctorSelect || !appointmentDate || !slotContainer) return;
        const doctorId = doctorSelect.value;
        const dateVal = appointmentDate.value;

        if (selectedSlotInput) selectedSlotInput.value = '';
        if (submitBtn) submitBtn.disabled = true;

        if (!doctorId || !dateVal) {
            slotContainer.innerHTML = '<span class="text-muted small">Please select both specialist and date to view time slots.</span>';
            return;
        }

        slotContainer.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div> <span class="text-muted ms-2 small">Calculating availability...</span>';

        fetch(`/api/available-slots?doctor_id=${doctorId}&date=${dateVal}`)
            .then(res => res.json())
            .then(data => {
                slotContainer.innerHTML = '';
                if (data.status === 'unavailable') {
                    slotContainer.innerHTML = `<div class="alert alert-warning py-2 px-3 small mb-0 w-100"><i class="bi bi-calendar-x me-1"></i> ${data.message}</div>`;
                    return;
                }

                if (data.status === 'success' && data.slots.length > 0) {
                    const row = document.createElement('div');
                    row.className = 'd-flex flex-wrap gap-2 w-100';

                    let hasAvailable = false;
                    data.slots.forEach(slot => {
                        const btn = document.createElement('button');
                        btn.type = 'button';
                        btn.textContent = slot.display;
                        btn.dataset.time = slot.time;

                        if (slot.is_available) {
                            hasAvailable = true;
                            btn.className = 'btn btn-outline-cp-navy btn-sm slot-btn rounded-pill px-3 py-2 fw-semibold';
                            btn.addEventListener('click', function () {
                                document.querySelectorAll('.slot-btn').forEach(b => {
                                    b.classList.remove('btn-cp-teal', 'text-white', 'shadow-sm');
                                    b.classList.add('btn-outline-cp-navy');
                                });
                                this.classList.remove('btn-outline-cp-navy');
                                this.classList.add('btn-cp-teal', 'text-white', 'shadow-sm');

                                selectedSlotInput.value = this.dataset.time;
                                if (submitBtn) submitBtn.disabled = false;
                            });
                        } else {
                            btn.className = 'btn btn-light btn-sm text-muted rounded-pill px-3 py-1 border';
                            btn.disabled = true;
                            btn.title = slot.reason === 'Booked' ? 'Slot already reserved' : 'Time has passed';
                        }
                        row.appendChild(btn);
                    });

                    if (!hasAvailable) {
                        slotContainer.innerHTML = '<div class="alert alert-secondary py-2 px-3 small mb-0 w-100"><i class="bi bi-clock me-1"></i> All slots for this date are fully booked or have passed. Please select another date.</div>';
                    } else {
                        slotContainer.appendChild(row);
                    }
                } else {
                    slotContainer.innerHTML = '<div class="alert alert-secondary py-2 px-3 small mb-0 w-100">No slots available for this date.</div>';
                }
            })
            .catch(err => {
                console.error('Error fetching slots:', err);
                slotContainer.innerHTML = '<div class="text-danger small">Error calculating slots. Please try again.</div>';
            });
    }
});
