/* Contains the functions for the dashboard filtering options

Copyright (c) 2024-present Hannah Esther Augustijn, MSc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

export function getFeaturesWithinRange(sampleData, minScore, maxScore, findFeatureId,
                                       minPhenotypeScore, maxPhenotypeScore, showOnlyPhenotypeFeatures,
                                       minMatchScore, maxMatchScore, showOnlyMatchFeatures,
                                       showOnlyAnnotationFeatures, showOnlyBlankFeatures,
                                       minMzScore, maxMzScore, minSampleCount, maxSampleCount,
                                       foldScore, foldGroup1, foldGroup2, foldSelectGroup,
                                       groupFilterValues, networkFilterValues, statsFIdGroups, networkType) {
    return sampleData.novScore.reduce((count, score, index) => {
        const phenotypeScore = sampleData.annotations?.[index]?.phenotypes?.[0]?.score;
        const matchScore = sampleData.annotations?.[index]?.matches?.[0]?.score;
        const annotation = sampleData.annotations?.[index]?.adducts ?? null;
        const mz = sampleData.precMz[index];
        const blanks = sampleData.blankAs?.[index];
        const findFeature = sampleData.featureId?.[index];
        const sampleCount = sampleData.samples[index].length;
        const foldChanges = sampleData.fGroupData?.[index]?.[foldSelectGroup] ?? [];
        const featureGroups = Object(statsFIdGroups)?.[findFeature] ?? [];
        const networkFIds = networkType === 'modified_cosine' ? sampleData.fNetworkCosine?.[index] ?? [] : sampleData.fNetworkDeepScore?.[index] ?? [];

        const groupFilterValid = groupFilterValues ? groupFilterValues.some(value => featureGroups.includes(value)) : true;
        const featureIdToBlankId = Object.fromEntries(
            sampleData.featureId.map((id, index) => [id, sampleData.blankAs?.[index]])
        );
        const networkFilterValid = networkFilterValues ? (networkFIds.length > 0 && !networkFIds.some(id =>
            networkFilterValues.some(value =>
                (value === "blanks" && featureIdToBlankId[id] === true) ||
                (statsFIdGroups[id] && statsFIdGroups[id].includes(value))
            ))) : true;

        let foldValid = !foldScore || !foldGroup1 || !foldGroup2 || !foldSelectGroup;
        if (!foldValid) {
            for (const foldChange of foldChanges) {
                if ((foldChange.group1 === foldGroup1 && foldChange.group2 === foldGroup2) ||
                    (foldChange.group1 === foldGroup2 && foldChange.group2 === foldGroup1)) {
                    if (foldChange.factor >= foldScore) {
                        foldValid = true;
                        break;
                    }
                }
            }
        }

        if ((score >= minScore && score <= maxScore) &&
            (!showOnlyPhenotypeFeatures || (phenotypeScore !== null && phenotypeScore >= minPhenotypeScore && phenotypeScore <= maxPhenotypeScore)) &&
            (!showOnlyMatchFeatures || (matchScore !== null && matchScore >= minMatchScore && matchScore <= maxMatchScore)) &&
            (!showOnlyAnnotationFeatures || (annotation !== null)) &&
            (!showOnlyBlankFeatures || (blanks !== true)) &&
            (!findFeatureId || (findFeatureId === findFeature)) &&
            (!maxMzScore || (mz >= minMzScore && mz <= maxMzScore)) &&
            (!maxSampleCount || (sampleCount >= minSampleCount && sampleCount <= maxSampleCount))
            && foldValid && groupFilterValid && networkFilterValid
            ) {
            return count + 1;
        }
        return count;
    }, 0);
}

export function getFilterGroupSelectionFields(statsGroups) {
    const selectFoldInput = document.getElementById('selectFoldInput');
    const group1FoldInput = document.getElementById('group1FoldInput');
    const group2FoldInput = document.getElementById('group2FoldInput');

    selectFoldInput.innerHTML = '<option value="null" selected>select group</option>';
    Object.keys(statsGroups).forEach(groupKey => {
        const option = document.createElement('option');
        option.value = groupKey;
        option.textContent = groupKey;
        selectFoldInput.appendChild(option);
    });

    selectFoldInput.addEventListener('change', () => {
        const selectedGroup = selectFoldInput.value;
        if (selectedGroup !== "null") {
            const groupValues = statsGroups[selectedGroup];

            group1FoldInput.innerHTML = '<option value="" selected>group 1</option>';
            groupValues.forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                group1FoldInput.appendChild(option);
            });

            group2FoldInput.innerHTML = '<option value="" selected>group 2</option>';
            groupValues.forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                group2FoldInput.appendChild(option);
            });

            group1FoldInput.disabled = false;
            group2FoldInput.disabled = false;
        } else {
            group1FoldInput.innerHTML = '<option value="" selected>group 1</option>';
            group2FoldInput.innerHTML = '<option value="" selected>group 2</option>';
            group1FoldInput.disabled = true;
            group2FoldInput.disabled = true;
        }
    });

    group1FoldInput.disabled = true;
    group2FoldInput.disabled = true;
}

export function populateDropdown(statsGroups) {
    const dropdownGroupContainer = document.getElementById('dropdownGroupContainer');
    const dropdownNetworkContainer = document.getElementById('dropdownNetworkContainer');
    const multiSelectGroup = dropdownGroupContainer.querySelector('select');
    const multiSelectNetwork = dropdownNetworkContainer.querySelector('select');

    // Clear previous options
    multiSelectGroup.innerHTML = '';
    multiSelectNetwork.innerHTML = '';

    // Add deselect option to network select
    const deselectOptionNetwork = document.createElement('option');
    deselectOptionNetwork.value = '';
    deselectOptionNetwork.textContent = 'Select group';
    multiSelectNetwork.appendChild(deselectOptionNetwork);

    const deselectOptionGroup = document.createElement('option');
    deselectOptionGroup.value = '';
    deselectOptionGroup.textContent = 'Select group';
    multiSelectGroup.appendChild(deselectOptionGroup);

    // Add "blanks" option to network select
    const blanksOption = document.createElement('option');
    blanksOption.value = 'blanks';
    blanksOption.textContent = 'Blanks';
    multiSelectNetwork.appendChild(blanksOption);

    Object.keys(statsGroups).forEach(groupKey => {
        // Create disabled group option for Group select
        const groupOptionGroup = document.createElement('option');
        groupOptionGroup.textContent = groupKey;
        groupOptionGroup.disabled = true;
        multiSelectGroup.appendChild(groupOptionGroup);

        // Create disabled group option for Network select
        const groupOptionNetwork = document.createElement('option');
        groupOptionNetwork.textContent = groupKey;
        groupOptionNetwork.disabled = true;
        multiSelectNetwork.appendChild(groupOptionNetwork);

        // Add the values under the respective group label
        statsGroups[groupKey].forEach(value => {
            // Create option for Group select
            const optionGroup = document.createElement('option');
            optionGroup.value = value;
            optionGroup.textContent = value;
            multiSelectGroup.appendChild(optionGroup);

            // Create option for Network select
            const optionNetwork = document.createElement('option');
            optionNetwork.value = value;
            optionNetwork.textContent = value;
            multiSelectNetwork.appendChild(optionNetwork);
        });
    });

    // Event listeners for deselecting all options
    multiSelectGroup.addEventListener('change', function(event) {
        if (event.target.value === '') {
            Array.from(multiSelectGroup.options).forEach(option => {
                option.selected = false;
            });
        }
    });

    multiSelectNetwork.addEventListener('change', function(event) {
        if (event.target.value === '') {
            Array.from(multiSelectNetwork.options).forEach(option => {
                option.selected = false;
            });
        }
    });
}