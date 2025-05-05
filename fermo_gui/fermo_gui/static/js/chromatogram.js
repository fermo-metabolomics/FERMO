/* Creates the Plotly elements for chromatogram drawing

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

export function visualizeData(sampleData, networkType = "modified_cosine",
                              isFeatureVisualization = false, minScore = 0, maxScore = 10, findFeatureId = false,
                              minPhenotypeScore = 0, maxPhenotypeScore = 1, showOnlyPhenotypeFeatures = false,
                              minMatchScore = 0, maxMatchScore = 1, showOnlyMatchFeatures = false,
                              showOnlyAnnotationFeatures = false, showOnlyBlankFeatures = false,
                              minMzScore = 0, maxMzScore = false,
                              minSampleScore = 0, maxSampleScore = false,
                              foldScore = null, foldGroup1 = false, foldGroup2 = false, foldSelectGroup = false,
                              groupFilterValues = null, networkFilterValues = null, statsFIdGroups = null) {
    const data = [];
    const maxPeaksPerSample = sampleData.traceInt.map(trace => Math.max(...trace));
    if (maxPeaksPerSample.length === 0 || maxPeaksPerSample.every(peak => isNaN(peak))) {
        Plotly.purge('featureChromatogram');
        return;
    } else {
        const combinedData = sampleData.traceRt.map((rt, i) => ({
            traceRt: rt,
            traceInt: sampleData.traceInt[i],
            featureId: sampleData.featureId[i],
            maxPeak: maxPeaksPerSample[i],
            chromColors: getChromColors(sampleData, i, isFeatureVisualization),
            toolTip: getToolTip(sampleData, i),
            novScore: sampleData.novScore[i],
            phenotypeScore: sampleData.annotations?.[i]?.phenotypes?.[0]?.score ?? null,
            matchScore: sampleData.annotations?.[i]?.matches?.[0]?.score ?? null,
            annId: sampleData.annotations?.[i]?.adducts ?? null,
            blankId: sampleData.blankAs?.[i] ?? null,
            mz: sampleData.precMz[i],
            sampleCount: sampleData.samples?.[i].length ?? null,
            foldChange: sampleData.fGroupData?.[i]?.[foldSelectGroup] ?? [],
            featureGroups: Object(statsFIdGroups)?.[sampleData.featureId[i]] ?? [],
            networkFIds: networkType === 'modified_cosine' ? sampleData.fNetworkCosine?.[i] ?? [] : sampleData.fNetworkDeepScore?.[i] ?? []
        })).sort((a, b) => b.maxPeak - a.maxPeak);

        combinedData.forEach(dataItem => {
            const result = {
                showlegend: false,
                x: dataItem.traceRt,
                y: dataItem.traceInt,
                type: 'scatter',
                mode: 'lines',
                name: `${dataItem.featureId}`,
                text: dataItem.toolTip,
                hoverinfo: 'text',
                hoverlabel: { bgcolor: '#41454c' },
                fill: 'toself',
                fillcolor: dataItem.chromColors.fillCol,
                line: {
                    color: dataItem.chromColors.lineCol,
                    width: 2,
                    shape: 'spline',
                    smoothing: 0.8,
                },
            };

            // Fold Score validation
            let foldValid = foldScore === null || !foldSelectGroup || !foldGroup1 || !foldGroup2;
            if (!foldValid) {
                for (const foldChange of dataItem.foldChange) {
                    if ((foldChange.group1 === foldGroup1 && foldChange.group2 === foldGroup2) ||
                        (foldChange.group1 === foldGroup2 && foldChange.group2 === foldGroup1)) {
                        if (foldChange.factor >= foldScore) {
                            foldValid = true;
                            break;
                        }
                    }
                }
            }
            const groupFilterValid = groupFilterValues ?
            groupFilterValues.some(value => dataItem.featureGroups.includes(value)) : true;

            const featureIdToBlankId = Object.fromEntries(
                sampleData.featureId.map((id, index) => [id, sampleData.blankAs?.[index]])
            );
            const networkFilterValid = networkFilterValues ? (dataItem.networkFIds.length > 0
            && !dataItem.networkFIds.some(id =>
                networkFilterValues.some(value =>
                    (value === "blanks" && featureIdToBlankId[id] === true) ||
                    (statsFIdGroups[id] && statsFIdGroups[id].includes(value))
                ))) : true;

            if (!isFeatureVisualization &&
                ((dataItem.novScore < minScore || dataItem.novScore > maxScore) ||
                (showOnlyPhenotypeFeatures && (dataItem.phenotypeScore === null ||
                dataItem.phenotypeScore < minPhenotypeScore || dataItem.phenotypeScore > maxPhenotypeScore)) ||
                (showOnlyMatchFeatures && (dataItem.matchScore === null ||
                dataItem.matchScore < minMatchScore || dataItem.matchScore > maxMatchScore)) ||
                (showOnlyAnnotationFeatures && (dataItem.annId === null)) ||
                (showOnlyBlankFeatures && (dataItem.blankId === true)) ||
                (findFeatureId && (dataItem.featureId !== findFeatureId)) ||
                (maxMzScore && (dataItem.mz < minMzScore || dataItem.mz > maxMzScore)) ||
                (maxSampleScore && (dataItem.sampleCount < minSampleScore || dataItem.sampleCount > maxSampleScore)) ||
                !foldValid || !groupFilterValid || !networkFilterValid
                )) {
                result.line.color = 'rgba(212, 212, 212, 0.8)';
                result.fillcolor = 'rgba(212, 212, 212, 0.3)';
            }
            data.push(result);
        });

        const { legLab, lineCol, fillCol } = getChromColors(sampleData, false, isFeatureVisualization);
        legLab.forEach((label, i) => data.push(createLegendItem(label, fillCol[i], lineCol[i], 'square')));
        if (!isFeatureVisualization) {
            data.push(createLegendItem('Unique to sample', '#000000'));
            data.push(createLegendItem('Selected feature', '#960303'));
        }

        const layout = {
            height: isFeatureVisualization ? 125 : 227,
            margin: { l: 50, r: 0, t: 0, b: isFeatureVisualization ? 35 : 30 },
            xaxis: {
                autorange: false,
                showgrid: false,
                visible: true,
                range: sampleData.upLowRange,
                title: isFeatureVisualization ? 'Retention time (min)' : false,
                titlefont: isFeatureVisualization ? { family: 'Arial', size: 12, color: 'grey' } : false
            },
            yaxis: {
                autorange: false,
                showgrid: false,
                range: [0, 1.05],
                linecolor: 'black',
                zeroline: true,
                zerolinewidth: 0.5,
                zerolinecolor: 'black',
                title: isFeatureVisualization ? 'Rel. intensity' : 'Relative intensity',
                titlefont: { family: 'Arial', size: 12, color: 'grey' },
            },
        };

        const plotId = isFeatureVisualization ? 'featureChromatogram' : 'mainChromatogram';
        Plotly.newPlot(plotId, data, layout);
    }
}

export function addBoxVisualization(traceInt, traceRt) {
    const boxSizeX = 0.12;
    const boxSizeY = 0.04;
    const maxInt = Math.max(...traceInt);
    const maxRt = Math.max(...traceRt);
    const minRt = Math.min(...traceRt);

    const update = {
        shapes: [{
            type: 'rect',
            mode: 'lines',
            xref: 'x',
            yref: 'y',
            x0: minRt - boxSizeX,
            y0: 0,
            x1: maxRt + boxSizeX,
            y1: maxInt + boxSizeY,
            line: { color: '#960303', width: 2.5, dash: 'dash' }
        }]
    };
    Plotly.relayout('mainChromatogram', update);
}

function createLegendItem(name, color, lineCol, type = 'line') {
    return {
        x: [null],
        y: [null],
        mode: 'markers',
        name: name,
        showlegend: true,
        marker: type === 'line' ? {
            size: 8,
            symbol: 'line-ew',
            line: { color: color, width: 2 }
        } : {
            size: 10,
            symbol: 'square',
            color: color,
            line: { color: lineCol, width: 2 }
        }
    };
}

function getChromColors(sampleData, peakNumber, isFeatureVisualization) {
    const colors = {
        default: {
            fillColors: ['rgba(153, 191, 159, 0.70)', 'rgba(252, 224, 151, 0.70)'],
            lineColors: ['#5a755e', '#fab80f'],
            legendLabels: ['Selected', 'Blank']
        },
        feature: {
            fillColors: ['rgba(245, 127, 129, 0.70)', 'rgba(66, 135, 245, 0.30)'],
            lineColors: ['#960303', '#127aa3'],
            legendLabels: ['Selected feature', 'Related feature']
        }
    };

    const colorSet = isFeatureVisualization ? colors.feature : colors.default;

    if (peakNumber === false || peakNumber === undefined) {
        return { legLab: colorSet.legendLabels, lineCol: colorSet.lineColors, fillCol: colorSet.fillColors };
    }

    if (!isFeatureVisualization) {
        const isBlank = sampleData.blankAs[peakNumber];
        const isSingleSample = sampleData.samples[peakNumber].length === 1;
        const index = isBlank ? 1 : 0;
        return {
            lineCol: isSingleSample ? '#000000' : colorSet.lineColors[index],
            fillCol: colorSet.fillColors[index]
        };
    } else {
        const targetType = sampleData.target[peakNumber];
        if (targetType === 'selected') {
            return { lineCol: colorSet.lineColors[0], fillCol: colorSet.fillColors[0] };
        } else if (targetType === 'related') {
            return { lineCol: colorSet.lineColors[1], fillCol: colorSet.fillColors[1] };
        }
    }
}

function getToolTip(sampleData, peakNumber) {
    return `&nbsp;Feature ID: ${sampleData.featureId[peakNumber]}<br>
            Precursor m/z: ${sampleData.precMz[peakNumber]}<br>
            Retention time: ${sampleData.retTime[peakNumber]}<br>
            Relative intensity: ${sampleData.relInt[peakNumber]}<br>
            Absolute intensity: ${sampleData.absInt[peakNumber]}<br>`;
}