/* Manages dashboard loading and initializes interactive elements

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

import { getSampleData, getFeatureData } from './parsing.js';
import { updateFeatureTables, hideTables, clearHeatmaps } from './dynamic_tables.js';
import { visualizeData, addBoxVisualization } from './chromatogram.js';
import { visualizeNetwork, hideNetwork } from './network.js';
import { enableDragAndDrop, disableDragAndDrop } from './dragdrop.js';
import { getFeaturesWithinRange, getFilterGroupSelectionFields, populateDropdown } from './filters.js';

document.addEventListener('DOMContentLoaded', function() {
    let dragged;
    let currentBoxParams = null;
    let sampleData;
    let statsChromatogram;
    let statsNetwork;
    let statsGroups;
    let clickedOnPoint = false;

    const getCurrentBoxParams = () => currentBoxParams;

    const allowDragAndDropCheckbox = document.getElementById('allowDragAndDrop');
    allowDragAndDropCheckbox.checked ? enableDragAndDrop() : disableDragAndDrop();

    allowDragAndDropCheckbox.addEventListener('change', function() {
        this.checked ? enableDragAndDrop() : disableDragAndDrop();
    });

    const chromatogramElement = document.getElementById('mainChromatogram');
    const networkElement = document.getElementById('cy');
    const groupElement = document.getElementById('groupInfo');
    const featureGroupElement = document.getElementById('statsFIdGroups');
    statsChromatogram = JSON.parse(chromatogramElement.getAttribute('data-stats-chromatogram'));
    statsNetwork = JSON.parse(networkElement.getAttribute('data-stats-network'));
    statsGroups = JSON.parse(groupElement.getAttribute('data-stats-groups'));
    const statsFIdGroups = JSON.parse(featureGroupElement.getAttribute('data-stats-fgroups'));

    const firstSample = document.querySelector('.select-sample');
    if (firstSample) {
        const firstSampleName = firstSample.getAttribute('data-sample-name');
        sampleData = getSampleData(firstSampleName, statsChromatogram);
        document.getElementById('activeSample').textContent = `Sample: ${firstSampleName}`;

        const networkType = 'modified_cosine';

        getFilterGroupSelectionFields(statsGroups);
        populateDropdown(statsGroups);

        Plotly.newPlot(chromatogramElement, []).then(() => {

            chromatogramElement.addEventListener('click', function(evt) {
                var bb = evt.target.getBoundingClientRect();
                var x = chromatogramElement._fullLayout.xaxis.p2d(evt.clientX - bb.left);
                var y = chromatogramElement._fullLayout.yaxis.p2d(evt.clientY - bb.top);

                if (!clickedOnPoint) {
                    unselectFeature();
                }
                clickedOnPoint = false;
            });

            document.getElementById('networkSelect').addEventListener('change', handleNetworkTypeChange);
            document.getElementById('showBlankFeatures').addEventListener('change', updateRange);
            document.getElementById('findInput').addEventListener('input', updateRange);
            document.getElementById('mz1Input').addEventListener('input', updateRange);
            document.getElementById('mz2Input').addEventListener('input', updateRange);
            document.getElementById('sample1Input').addEventListener('input', updateRange);
            document.getElementById('sample2Input').addEventListener('input', updateRange);
            document.getElementById('foldInput').addEventListener('input', updateRange);
            document.getElementById('group1FoldInput').addEventListener('input', updateRange);
            document.getElementById('group2FoldInput').addEventListener('input', updateRange);
            document.getElementById('selectFoldInput').addEventListener('change', updateRange);
            document.getElementById('groupFilter').addEventListener('change', updateRange);
            document.getElementById('networkFilter').addEventListener('change', updateRange);
            document.getElementById('showAnnotationFeatures').addEventListener('change', function() {
                const isChecked = this.checked;
                updateRange();
                document.querySelectorAll('.annotation-related').forEach(container => {
                    container.style.display = isChecked ? 'block' : 'none';
                });
            });

            document.getElementById('resetFilters').addEventListener('click', resetFilters);

            updateRange();
        });
    }

    function handleChromatogramClick(data) {
        clearHeatmaps();
        const networkType = document.getElementById('networkSelect').value;
        const featureId = data.points[0].data.name;
        const filteredSampleData = getFeatureData(featureId, sampleData, networkType);
        const sampleId = updateFeatureTables(featureId, sampleData, filteredSampleData);
        currentBoxParams = { traceInt: sampleData.traceInt[sampleId], traceRt: sampleData.traceRt[sampleId] };
        addBoxVisualization(currentBoxParams.traceInt, currentBoxParams.traceRt);
        visualizeNetwork(featureId, statsNetwork, filteredSampleData, sampleData, sampleId, statsChromatogram, networkType);
    }

    function unselectFeature() {
        clearHeatmaps();
        hideNetwork();
        hideTables();
        document.getElementById('feature-general-info').textContent =
        'Click on any feature in the main chromatogram overview.';
        document.getElementById('feature-annotation').textContent =
        'Click on any feature in the main chromatogram overview.';
        currentBoxParams = null;
        Plotly.purge('featureChromatogram');
        Plotly.relayout(chromatogramElement, { shapes: [] });
    }

    function handleNetworkTypeChange() {
        const networkType = document.getElementById('networkSelect').value;
        const featureId = document.getElementById('activeFeature').textContent.split(': ')[1];
        const filteredSampleData = getFeatureData(featureId, sampleData, networkType);
        const sampleId = updateFeatureTables(featureId, sampleData, filteredSampleData);
        updateRange();
        currentBoxParams = { traceInt: sampleData.traceInt[sampleId], traceRt: sampleData.traceRt[sampleId] };
        visualizeNetwork(featureId, statsNetwork, filteredSampleData, sampleData, sampleId, statsChromatogram, networkType);
    }

    function toggleDropdown(containerId) {
        const dropdownContainer = document.getElementById(containerId);
        dropdownContainer.style.display = (dropdownContainer.style.display === "none" || dropdownContainer.style.display === "") ? "block" : "none";
    }

    function checkAndEnableOption(jobId, filename, elementId) {
        const url = `/check_file/${jobId}/${filename}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const element = document.getElementById(elementId);
                if (data.exists) {
                    element.disabled = false;
                    element.dataset.url = `/download/${jobId}/${filename}`;
                } else {
                    element.disabled = true;
                    delete element.dataset.url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    const jobId = document.querySelector('.container').getAttribute('data-job-id');

    // Check and enable options based on file availability
    checkAndEnableOption(jobId, 'out.fermo.summary.txt', 'summary');
    checkAndEnableOption(jobId, 'out.fermo.abbrev.csv', 'abbrev');
    checkAndEnableOption(jobId, 'out.fermo.log', 'log');
    checkAndEnableOption(jobId, 'out.fermo.session.json', 'session');
    checkAndEnableOption(jobId, 'out.fermo.full.csv', 'full');
    checkAndEnableOption(jobId, 'out.fermo.modified_cosine.graphml', 'mod_cosine');
    checkAndEnableOption(jobId, 'out.fermo.ms2deepscore.graphml', 'ms2deepscore');

    // Add event listeners to download buttons
    document.querySelectorAll('.download-btn').forEach(function(button) {
        button.addEventListener('click', function(event) {
            const selectId = event.target.getAttribute('data-select-id');
            const selectElement = document.getElementById(selectId);
            const selectedOption = selectElement.selectedOptions[0];
            if (selectedOption && selectedOption.dataset.url) {
                window.location.href = selectedOption.dataset.url;
            } else {
                alert('Please select a file to download.');
            }
        });
    });
    document.getElementById('groupButton').addEventListener('click', () => toggleDropdown('dropdownGroupContainer'));
    document.getElementById('networkExcludeButton').addEventListener('click', () => toggleDropdown('dropdownNetworkContainer'));

    document.querySelectorAll('.select-sample').forEach(row => {
        row.addEventListener('click', function() {
            const sampleName = this.getAttribute('data-sample-name');
            sampleData = getSampleData(sampleName, statsChromatogram);
            hideNetwork();
            hideTables();
            document.getElementById('activeSample').textContent = `Sample: ${sampleName}`;
            Plotly.purge('featureChromatogram');
            document.getElementById('feature-general-info').textContent =
            'Click on any feature in the main chromatogram overview.';
            document.getElementById('feature-annotation').textContent =
            'Click on any feature in the main chromatogram overview.';
            clearHeatmaps();
            const networkType = 'modified_cosine';
            currentBoxParams = null;

            initializeFilters(visualizeData, handleChromatogramClick, addBoxVisualization, updateRetainedFeatures,
                sampleData, chromatogramElement, getCurrentBoxParams);

            updateRange();
        });
    });

    function updateRange() {
        const chromatogramElement = document.getElementById('mainChromatogram');
        let currentXRange = chromatogramElement.layout.xaxis.range;
        let currentYRange = chromatogramElement.layout.yaxis.range;

        const minScore = parseFloat(document.getElementById('noveltyRange1').value);
        const maxScore = parseFloat(document.getElementById('noveltyRange2').value);
        const minPhenotypeScore = parseFloat(document.getElementById('phenotypeRange1').value);
        const maxPhenotypeScore = parseFloat(document.getElementById('phenotypeRange2').value);
        const showOnlyPhenotypeFeatures = document.getElementById('showPhenotypeFeatures').checked;
        const minMatchScore = parseFloat(document.getElementById('matchRange1').value);
        const maxMatchScore = parseFloat(document.getElementById('matchRange2').value);
        const showOnlyMatchFeatures = document.getElementById('showMatchFeatures').checked;
        const showOnlyAnnotationFeatures = document.getElementById('showAnnotationFeatures').checked;
        const showOnlyBlankFeatures = document.getElementById('showBlankFeatures').checked;
        const findFeatureId = parseFloat(document.getElementById('findInput').value);
        const minMzScore = parseFloat(document.getElementById('mz1Input').value);
        const maxMzScore = parseFloat(document.getElementById('mz2Input').value);
        const minSampleCount = parseFloat(document.getElementById('sample1Input').value);
        const maxSampleCount = parseFloat(document.getElementById('sample2Input').value);
        const foldScore = parseFloat(document.getElementById('foldInput').value);
        const foldGroup1 = document.getElementById('group1FoldInput').value;
        const foldGroup2 = document.getElementById('group2FoldInput').value;
        const foldSelectGroup = document.getElementById('selectFoldInput').value;
        const networkType = document.getElementById('networkSelect').value;

        const groupFilterSelect = document.getElementById('groupFilter');
        const networkFilterSelect = document.getElementById('networkFilter');

        const groupFilterValues = Array.from(groupFilterSelect.selectedOptions).map(option => option.value);
        const networkFilterValues = Array.from(networkFilterSelect.selectedOptions).map(option => option.value);

        const foldScoreInputsFilled = foldScore && foldGroup1 && foldGroup2 && foldSelectGroup;

        visualizeData(sampleData, networkType, false, minScore, maxScore, findFeatureId,
                      minPhenotypeScore, maxPhenotypeScore, showOnlyPhenotypeFeatures,
                      minMatchScore, maxMatchScore, showOnlyMatchFeatures,
                      showOnlyAnnotationFeatures, showOnlyBlankFeatures,
                      minMzScore, maxMzScore ? maxMzScore : 10000,
                      minSampleCount, maxSampleCount ? maxSampleCount : 100,
                      foldScoreInputsFilled ? foldScore : null, foldGroup1, foldGroup2, foldSelectGroup,
                      groupFilterValues.length ? groupFilterValues : null,
                      networkFilterValues.length ? networkFilterValues : null, statsFIdGroups);

        if (currentXRange[0] < 0) {
            currentXRange = chromatogramElement.layout.xaxis.range;
            currentYRange = chromatogramElement.layout.yaxis.range;
        }

        chromatogramElement.on('plotly_click', function(data) {
            clickedOnPoint = true;
            handleChromatogramClick(data);
        });

        const featureId = document.getElementById('activeFeature').textContent.split(': ')[1];
        for (var i = 0; i < sampleData.featureId.length; i++) {
            if (sampleData.featureId[i] == featureId) {
                var currentBoxParams = { traceInt: sampleData.traceInt[i], traceRt: sampleData.traceRt[i] };
            }
        }

        if (currentBoxParams) {
            addBoxVisualization(currentBoxParams.traceInt, currentBoxParams.traceRt);
        }

        updateRetainedFeatures(minScore, maxScore, findFeatureId,
                               minPhenotypeScore, maxPhenotypeScore, showOnlyPhenotypeFeatures,
                               minMatchScore, maxMatchScore, showOnlyMatchFeatures,
                               showOnlyAnnotationFeatures, showOnlyBlankFeatures,
                               minMzScore, maxMzScore, minSampleCount, maxSampleCount,
                               foldScoreInputsFilled ? foldScore : null, foldGroup1, foldGroup2, foldSelectGroup,
                               groupFilterValues.length ? groupFilterValues : null,
                               networkFilterValues.length ? networkFilterValues : null, statsFIdGroups);

        Plotly.relayout(chromatogramElement, {
            'xaxis.range': currentXRange,
            'yaxis.range': currentYRange
        });
    }

    function updateRetainedFeatures(minScore, maxScore, findFeatureId,
                                    minPhenotypeScore, maxPhenotypeScore, showOnlyPhenotypeFeatures,
                                    minMatchRange, maxMatchRange, showOnlyMatchFeatures,
                                    showAnnotationFeatures, showBlankFeatures,
                                    minMzScore, maxMzScore, minSampleScore, maxSampleScore,
                                    foldScore, foldGroup1, foldGroup2, foldSelectGroup,
                                    groupFilterValues, networkFilterValues, statsFIdGroups) {
        document.querySelectorAll('.select-sample').forEach(row => {
            const sampleName = row.getAttribute('data-sample-name');
            const sampleData = getSampleData(sampleName, statsChromatogram);
            const featuresWithinRange = getFeaturesWithinRange(sampleData, minScore, maxScore, findFeatureId,
                minPhenotypeScore, maxPhenotypeScore, showOnlyPhenotypeFeatures,
                minMatchRange, maxMatchRange, showOnlyMatchFeatures,
                showAnnotationFeatures, showBlankFeatures,
                minMzScore, maxMzScore, minSampleScore, maxSampleScore,
                foldScore, foldGroup1, foldGroup2, foldSelectGroup,
                groupFilterValues, networkFilterValues, statsFIdGroups);
            row.children[2].textContent = featuresWithinRange;
        });
    }

    function initializeFilters(visualizeData, handleChromatogramClick, addBoxVisualization, updateRetainedFeatures,
                                  sampleData, chromatogramElement, getCurrentBoxParams) {
        const elements = {
            noveltyRange1: document.getElementById('noveltyRange1'),
            noveltyRange2: document.getElementById('noveltyRange2'),
            noveltyRange1Input: document.getElementById('noveltyRange1Input'),
            noveltyRange2Input: document.getElementById('noveltyRange2Input'),
            phenotypeRange1: document.getElementById('phenotypeRange1'),
            phenotypeRange2: document.getElementById('phenotypeRange2'),
            phenotypeRange1Input: document.getElementById('phenotypeRange1Input'),
            phenotypeRange2Input: document.getElementById('phenotypeRange2Input'),
            showPhenotypeFeatures: document.getElementById('showPhenotypeFeatures'),
            matchRange1: document.getElementById('matchRange1'),
            matchRange2: document.getElementById('matchRange2'),
            matchRange1Input: document.getElementById('matchRange1Input'),
            matchRange2Input: document.getElementById('matchRange2Input'),
            showMatchFeatures: document.getElementById('showMatchFeatures'),
            showAnnotationFeatures: document.getElementById('showAnnotationFeatures'),
            showBlankFeatures: document.getElementById('showBlankFeatures')
        };

        function enforceConstraints() {
            if (parseFloat(elements.noveltyRange1Input.value) > parseFloat(elements.noveltyRange2Input.value)) {
                elements.noveltyRange1Input.value = elements.noveltyRange2Input.value;
            }
            if (parseFloat(elements.noveltyRange2Input.value) < parseFloat(elements.noveltyRange1Input.value)) {
                elements.noveltyRange2Input.value = elements.noveltyRange1Input.value;
            }
            if (parseFloat(elements.phenotypeRange1Input.value) > parseFloat(elements.phenotypeRange2Input.value)) {
                elements.phenotypeRange1Input.value = elements.phenotypeRange2Input.value;
            }
            if (parseFloat(elements.phenotypeRange2Input.value) < parseFloat(elements.phenotypeRange1Input.value)) {
                elements.phenotypeRange2Input.value = elements.phenotypeRange1Input.value;
            }
            if (parseFloat(elements.matchRange1Input.value) > parseFloat(elements.matchRange2Input.value)) {
                elements.matchRange1Input.value = elements.matchRange2Input.value;
            }
            if (parseFloat(elements.matchRange2Input.value) < parseFloat(elements.matchRange1Input.value)) {
                elements.matchRange2Input.value = elements.matchRange1Input.value;
            }
            updateRange();
        }

        const rangeElements = [
            { slider: elements.noveltyRange1, input: elements.noveltyRange1Input },
            { slider: elements.noveltyRange2, input: elements.noveltyRange2Input },
            { slider: elements.phenotypeRange1, input: elements.phenotypeRange1Input },
            { slider: elements.phenotypeRange2, input: elements.phenotypeRange2Input },
            { slider: elements.matchRange1, input: elements.matchRange1Input },
            { slider: elements.matchRange2, input: elements.matchRange2Input }
        ];

        rangeElements.forEach(({ slider, input }) => {
            slider.addEventListener('input', () => {
                input.value = slider.value;
                updateRange();
            });
            input.addEventListener('input', () => {
                slider.value = input.value;
                updateRange();
            });
            input.addEventListener('blur', enforceConstraints);
        });

        elements.showPhenotypeFeatures.addEventListener('change', updateRange);
        elements.showMatchFeatures.addEventListener('change', updateRange);

        updateRange();
    }


    function resetFilters() {
        // Reset all filter inputs to their default values
        document.getElementById('noveltyRange1').value = 0;
        document.getElementById('noveltyRange2').value = 10;
        document.getElementById('noveltyRange1Input').value = 0;
        document.getElementById('noveltyRange2Input').value = 1;
        document.getElementById('phenotypeRange1').value = 0;
        document.getElementById('phenotypeRange2').value = 1;
        document.getElementById('phenotypeRange1Input').value = 0;
        document.getElementById('phenotypeRange2Input').value = 1;
        document.getElementById('showPhenotypeFeatures').checked = false;
        document.getElementById('matchRange1').value = 0;
        document.getElementById('matchRange2').value = 1;
        document.getElementById('matchRange1Input').value = 0;
        document.getElementById('matchRange2Input').value = 1;
        document.getElementById('showMatchFeatures').checked = false;
        document.getElementById('showAnnotationFeatures').checked = false;
        document.getElementById('showBlankFeatures').checked = false;
        document.getElementById('findInput').value = '';
        document.getElementById('mz1Input').value = 0;
        document.getElementById('mz2Input').value = 10000;
        document.getElementById('sample1Input').value = 0;
        document.getElementById('sample2Input').value = 100;
        document.getElementById('foldInput').value = '';
        document.getElementById('group1FoldInput').value = '';
        document.getElementById('group2FoldInput').value = '';
        document.getElementById('selectFoldInput').value = 'null';
        document.getElementById('groupFilter').selectedIndex = -1;
        document.getElementById('networkFilter').selectedIndex = -1;
        updateRange();
    }

    initializeFilters(visualizeData, handleChromatogramClick, addBoxVisualization, updateRetainedFeatures,
        sampleData, chromatogramElement, getCurrentBoxParams);
});
