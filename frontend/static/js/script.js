document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('purchaseForm');
    const dateInput = document.getElementById('date');
    const billNoInput = document.getElementById('bill_no');
    const clearBtn = document.getElementById('clearBtn');

    const bags = document.getElementById('bags');
    const netWeight = document.getElementById('net_weight');
    const shortageKg = document.getElementById('shortage_kg');
    const avgBagWeight = document.getElementById('avg_bag_weight');
    const rate = document.getElementById('rate');
    const rateBasis = document.getElementById('rate_basis');
    const calculatedRate = document.getElementById('calculated_rate');
    const amount = document.getElementById('amount');
    const bankCommission = document.getElementById('bank_commission');
    const postage = document.getElementById('postage');
    const freight = document.getElementById('freight');
    const rateDiff = document.getElementById('rate_diff');
    const qualityDiff = document.getElementById('quality_diff');
    const moistureDed = document.getElementById('moisture_ded');
    const tds = document.getElementById('tds');
    const batavPercent = document.getElementById('batav_percent');
    const batav = document.getElementById('batav');
    const dalaliRate = document.getElementById('dalali_rate');
    const dalali = document.getElementById('dalali');
    const hammaliRate = document.getElementById('hammali_rate');
    const hammali = document.getElementById('hammali');
    const totalDeduction = document.getElementById('total_deduction');
    const payableAmount = document.getElementById('payable_amount');
    const paymentAmount = document.getElementById('payment_amount');

    dateInput.valueAsDate = new Date();
    fetchNextBillNo();

    function fetchNextBillNo() {
        fetch('/api/next-bill-no')
            .then(response => response.json())
            .then(data => {
                billNoInput.value = data.bill_no;
            })
            .catch(error => {
                console.error('Error fetching bill number:', error);
                billNoInput.value = '1';
            });
    }

    function calculateCalculatedRate() {
        const userRate100 = parseFloat(rate.value) || 0;
        const rateBasisVal = rateBasis.value;

        let calculatedRateVal;
        if (rateBasisVal === '100') {
            calculatedRateVal = userRate100;
        } else if (rateBasisVal === '150') {
            calculatedRateVal = (userRate100 / 2) * 3;
        }

        calculatedRate.value = calculatedRateVal.toFixed(2);
        return calculatedRateVal;
    }

    function calculateFields() {
        const bagsVal = parseFloat(bags.value) || 0;
        const netWeightVal = parseFloat(netWeight.value) || 0;
        const shortageKgVal = parseFloat(shortageKg.value) || 0;

        const bankCommissionVal = parseFloat(bankCommission.value) || 0;
        const postageVal = parseFloat(postage.value) || 0;
        const freightVal = parseFloat(freight.value) || 0;
        const rateDiffVal = parseFloat(rateDiff.value) || 0;
        const qualityDiffVal = parseFloat(qualityDiff.value) || 0;
        const moistureDedVal = parseFloat(moistureDed.value) || 0;
        const tdsVal = parseFloat(tds.value) || 0;

        const batavPercentVal = parseFloat(batavPercent.value) || 0;
        const dalaliRateVal = parseFloat(dalaliRate.value) || 0;
        const hammaliRateVal = parseFloat(hammaliRate.value) || 0;

        const calculatedRateVal = parseFloat(calculatedRate.value) || 0;

        const adjustedNetWeight = Math.max(0, netWeightVal - shortageKgVal);

        const avgBagWeightVal = bagsVal > 0 ? Math.round((adjustedNetWeight / bagsVal) * 100) / 100 : 0;
        avgBagWeight.value = avgBagWeightVal.toFixed(2);

        const amountVal = Math.round(adjustedNetWeight * calculatedRateVal * 100) / 100;

        const batavVal = batavPercentVal > 0 ? Math.round(amountVal * (batavPercentVal / 100) * 100) / 100 : 0;

        const dalaliVal = dalaliRateVal > 0 ? Math.round(adjustedNetWeight * dalaliRateVal * 100) / 100 : 0;
        const hammaliVal = hammaliRateVal > 0 ? Math.round(adjustedNetWeight * hammaliRateVal * 100) / 100 : 0;

        const categoryADeductions = bankCommissionVal + postageVal + freightVal + rateDiffVal + qualityDiffVal + moistureDedVal + tdsVal;
        const totalDeductionVal = Math.round((categoryADeductions + batavVal + dalaliVal + hammaliVal) * 100) / 100;

        const payableAmountVal = Math.round((amountVal - totalDeductionVal) * 100) / 100;

        amount.value = amountVal.toFixed(2);
        batav.value = batavVal.toFixed(2);
        dalali.value = dalaliVal.toFixed(2);
        hammali.value = hammaliVal.toFixed(2);
        totalDeduction.value = totalDeductionVal.toFixed(2);
        payableAmount.textContent = payableAmountVal.toFixed(2);
        paymentAmount.value = payableAmountVal.toFixed(2);
    }

    rate.addEventListener('input', function() {
        calculateCalculatedRate();
        calculateFields();
    });

    rateBasis.addEventListener('change', function() {
        calculateCalculatedRate();
        calculateFields();
    });

    netWeight.addEventListener('input', calculateFields);
    shortageKg.addEventListener('input', calculateFields);
    bags.addEventListener('input', calculateFields);

    document.querySelectorAll('.calc-input').forEach(input => {
        input.addEventListener('input', calculateFields);
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        const data = {};

        formData.forEach((value, key) => {
            data[key] = value;
        });

        const adjustedNetWeight = Math.max(0, parseFloat(netWeight.value) - parseFloat(shortageKg.value));
        data['net_weight'] = adjustedNetWeight.toFixed(2);
        data['shortage_kg'] = shortageKg.value;
        data['calculated_rate'] = calculatedRate.value;
        data['amount'] = amount.value;
        data['batav'] = batav.value;
        data['dalali'] = dalali.value;
        data['hammali'] = hammali.value;
        data['total_deduction'] = totalDeduction.value;
        data['payable_amount'] = payableAmount.textContent;

        try {
            const response = await fetch('/api/add-slip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                alert('Purchase slip saved successfully!');
                window.open(`/print/${result.slip_id}`, '_blank');
                form.reset();
                dateInput.valueAsDate = new Date();
                fetchNextBillNo();
                calculateFields();
            } else {
                alert('Error saving slip: ' + result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error saving purchase slip');
        }
    });

    clearBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the form?')) {
            form.reset();
            dateInput.valueAsDate = new Date();
            fetchNextBillNo();
            calculateFields();
        }
    });

    calculateCalculatedRate();
    calculateFields();

    // ===== DYNAMIC GODOWN DROPDOWN =====
    const godownInput = document.getElementById('paddy_unloading_godown');
    const godownDatalist = document.getElementById('godownList');
    let allGodowns = [];

    // Load existing godowns on page load
    async function loadGodowns() {
        try {
            const response = await fetch('/api/unloading-godowns');
            const result = await response.json();

            if (result.success) {
                allGodowns = result.godowns;
                updateGodownDatalist();
                console.log(`✓ Loaded ${allGodowns.length} godowns`);
            }
        } catch (error) {
            console.error('Error loading godowns:', error);
        }
    }

    // Update datalist with godown options
    function updateGodownDatalist() {
        godownDatalist.innerHTML = '';
        allGodowns.forEach(godown => {
            const option = document.createElement('option');
            option.value = godown.name;
            godownDatalist.appendChild(option);
        });
    }

    // Check if godown exists, if not add it
    async function handleGodownInput() {
        const enteredValue = godownInput.value.trim();

        if (!enteredValue) return;

        // Check if it already exists in the list
        const exists = allGodowns.some(g => g.name.toLowerCase() === enteredValue.toLowerCase());

        if (!exists) {
            // Add new godown to database
            try {
                const response = await fetch('/api/unloading-godowns', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: enteredValue })
                });

                const result = await response.json();

                if (result.success) {
                    console.log(`✓ Added new godown: ${enteredValue}`);
                    allGodowns = result.godowns; // Update with new list from server
                    updateGodownDatalist();
                }
            } catch (error) {
                console.error('Error adding godown:', error);
            }
        }
    }

    // Listen for when user finishes typing or selects an option
    godownInput.addEventListener('blur', handleGodownInput);

    // Also check when user presses Enter while focused on the field
    godownInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleGodownInput();
        }
    });

    // Load godowns when page loads
    loadGodowns();
});
