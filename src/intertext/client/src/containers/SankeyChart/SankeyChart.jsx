import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useHistory } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Card } from '@mui/material';
import _ from 'lodash';

import { getSearchResults, setFilters } from '../../store/actions/searchAction';
import { createSankeyChart } from '../../utils/sankeyChartUtils';
import { getDomain } from '../../utils/domainUtils';

import SubheaderCard from '../../components/SubheaderCard/SubheaderCard';
import ChartLegend from '../../components/ChartLegend/ChartLegend';
import CustomDivider from '../../components/CustomDivider/CustomDivider';

export const CHART_COLORS = ['#c6d7d1', '#f5d1c3', '#ffbaa8', '#c9d37f', '#f0bc68', '#609696'];
const CHART_ID = '#chart';

const SankeyChart = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [domain, setDomain] = useState();
  const {
    metadata,
    data: {
      matchIds,
      fileIdsByField: { title: fileIdsByTitle },
    },
    advancedSearchParams,
  } = useSelector(reduxState => reduxState.search);
  const dispatch = useDispatch();
  const history = useHistory();

  const handleSearch = searchParams => {
    const data = {
      ...advancedSearchParams,
      earlierText: { ...advancedSearchParams.earlierText, fileId: searchParams.sourceId },
      laterText: { ...advancedSearchParams.laterText, fileId: searchParams.targetId },
    };

    dispatch(setFilters(data));
    dispatch(getSearchResults(matchIds));
    history.push('/home');
  };

  const getChartData = (matches, idsByTitle) => {
    const isDataMissing =
      !matches || !Object.keys(matches).length || !idsByTitle || !Object.keys(idsByTitle).length;

    if (isDataMissing) {
      return;
    }

    const titlesByFileId = Object.entries(idsByTitle).reduce((result, [title, ids]) => {
      ids.forEach(id => {
        result[id] = title;
      });
      return result;
    }, {});

    const { chartNodes, linesByEarlierId } = matches.reduce(
      (result, [, earlierId, laterId, , , similarity]) => {
        const earlierNodeId = `earlier-${earlierId}`;
        const laterNodeId = `later-${laterId}`;
        const title = titlesByFileId[earlierId];

        const getProperty = (id, property) => metadata.find(work => work.id === id)[property];

        result.chartNodes[earlierNodeId] = {
          id: earlierId,
          nodeId: earlierNodeId,
          label: title,
          author: getProperty(earlierId, 'author'),
          year: getProperty(earlierId, 'year'),
        };

        result.chartNodes[laterNodeId] = {
          id: laterId,
          nodeId: laterNodeId,
          label: titlesByFileId[laterId],
          author: getProperty(laterId, 'author'),
          year: getProperty(laterId, 'year'),
        };

        const currentEarlierValues = result.linesByEarlierId[earlierNodeId];
        const defaultValue = {
          count: 0,
          similarity: [],
        };

        result.linesByEarlierId[earlierNodeId] = currentEarlierValues || {};
        result.linesByEarlierId[earlierNodeId][laterNodeId] =
          currentEarlierValues?.[laterNodeId] || defaultValue;
        result.linesByEarlierId[earlierNodeId][laterNodeId].count++;
        result.linesByEarlierId[earlierNodeId][laterNodeId].similarity.push(similarity);

        return result;
      },
      { chartNodes: {}, linesByEarlierId: {} }
    );

    const links = Object.keys(linesByEarlierId).reduce((result, currentEarlierId) => {
      Object.keys(linesByEarlierId[currentEarlierId]).forEach(currentLaterId => {
        result.push({
          source: currentEarlierId,
          target: currentLaterId,
          similarity: _.mean(linesByEarlierId[currentEarlierId][currentLaterId].similarity),
          value: linesByEarlierId[currentEarlierId][currentLaterId].count,
        });
      });
      return result;
    }, []);

    const data = {
      nodes: Object.values(chartNodes),
      links,
    };

    return data;
  };

  useEffect(() => {
    if (isLoaded || !matchIds.length || !fileIdsByTitle) {
      return;
    }

    const currentDomain = getDomain(matchIds, null, CHART_COLORS.length + 1);
    const chartData = getChartData(matchIds, fileIdsByTitle);

    setDomain(currentDomain);
    createSankeyChart({
      chartId: CHART_ID,
      chartData,
      domain: currentDomain.elements,
      onSearch: handleSearch,
    });
    setIsLoaded(true);
  }, [isLoaded, matchIds, fileIdsByTitle]);

  return (
    <div className="sankey-page content-page">
      <SubheaderCard>
        <span>
          <FormattedMessage id="sankeyVisualization.title" />
        </span>
      </SubheaderCard>
      <Card className="sankey-card">
        {domain?.elements.length > 0 && (
          <ChartLegend domainElements={domain?.elements} chartColors={CHART_COLORS} />
        )}
        <CustomDivider withIcon orientation="vertical" variant="middle" />
        <div id={CHART_ID.substring(1)} className="chart" />
      </Card>
    </div>
  );
};

export default SankeyChart;
