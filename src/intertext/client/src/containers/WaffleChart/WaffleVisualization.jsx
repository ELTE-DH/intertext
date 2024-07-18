import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { useLocation, useParams } from 'react-router-dom';
import { Card, Chip, Divider, ToggleButton, ToggleButtonGroup } from '@mui/material';

import {
  getChartData,
  getClickedElement,
  setClickedElement,
  setCurrentCardData,
  setVisualizedBy,
} from '../../store/actions/visualizationAction';

import Title from '../../components/Title/Title';
import CloseIcon from '../../components/Icons/CloseIcon';
import ResultPair from '../../components/ResultPair/ResultPair';
import ChartLegend from '../../components/ChartLegend/ChartLegend';
import SubheaderCard from '../../components/SubheaderCard/SubheaderCard';
import CustomDivider from '../../components/CustomDivider/CustomDivider';
import LoadingIndicator from '../../components/LoadingIndicator/LoadingIndicator';

import WaffleChart from './WaffleChart';

import { getDomain } from '../../utils/domainUtils';

export const CHART_COLORS = ['#c6d7d1', '#f5d1c3', '#ffbaa8', '#f0bc68', '#609696'];

const TOGGLE_OPTIONS = [
  { translationKey: 'author', value: 'author' },
  { translationKey: 'segment', value: 'segment' },
  { translationKey: 'year', value: 'year' },
];
const CHART_WIDTH = 500;
const CHART_HEIGHT = 250;

const WaffleVisualization = () => {
  const {
    chartData,
    columnCountsByXAxisValues,
    maxColumn,
    xAxisValues,
    width,
    chartMargin,
    marginBetweenColumns,
    clickedElement,
    visualizedBy,
    squareSize,
  } = useSelector(reduxState => reduxState.visualization);
  const { metadata } = useSelector(reduxState => reduxState.search);
  const [visualizeBy, setVisualizeBy] = useState(visualizedBy);
  const [workMetadata, setWorkMetadata] = useState();
  const [domain, setDomain] = useState();
  const dispatch = useDispatch();
  const { id } = useParams();
  const { search } = useLocation();
  const searchParams = new URLSearchParams(search);
  const type = searchParams.get('type');

  useEffect(() => {
    if (chartData.length) {
      const domainValues = getDomain(chartData, 'similarity', CHART_COLORS.length + 1);
      setDomain(domainValues);
    }
  }, [chartData]);

  useEffect(() => {
    if (!metadata.length) {
      return;
    }

    dispatch(setClickedElement({ clickedElement: null }));

    const currentMetadata = metadata.find(work => work.id.toString() === id);
    setWorkMetadata(currentMetadata);

    const { title, author, year } = currentMetadata;
    const payload = {
      type,
      file_id: id,
      title,
      author,
      year,
    };

    dispatch(setCurrentCardData(payload));
    dispatch(getChartData());
  }, [metadata, id]);

  const handleToggleChange = (_, newField) => {
    if (!newField) {
      return;
    }

    setVisualizeBy(newField);
    dispatch(setVisualizedBy({ visualizedBy: newField }));
    dispatch(getChartData());
  };

  const handleGetClickedElementData = id => {
    dispatch(getClickedElement(id));
  };

  const handleClose = () => {
    dispatch(setClickedElement({ clickedElement: null }));
  };

  return (
    <div className="waffle-page visualization-page content-page">
      <SubheaderCard>
        {workMetadata && (
          <Title author={workMetadata.author} year={workMetadata.year} title={workMetadata.title} />
        )}
      </SubheaderCard>
      <Card className="chart-card">
        <div className="details">
          <ToggleButtonGroup exclusive value={visualizeBy} onChange={handleToggleChange}>
            {TOGGLE_OPTIONS.map(({ value, translationKey }) => (
              <ToggleButton value={value} className={`${value}-button`}>
                <FormattedMessage id={`toggleButtons.${translationKey}`} />
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <CustomDivider withIcon orientation="horizontal" variant="middle" />
          {domain?.elements.length > 0 && (
            <ChartLegend domainElements={domain.elements} chartColors={CHART_COLORS} />
          )}
        </div>
        <div className="chart-container">
          {chartData.length > 0 && domain && domain.elements.length > 0 ? (
            <WaffleChart
              xAxisValues={xAxisValues}
              xAxisLabelRotation={30}
              squareSize={squareSize}
              width={width || CHART_WIDTH}
              height={CHART_HEIGHT}
              margin={chartMargin}
              marginBetweenColumns={marginBetweenColumns}
              chartData={chartData}
              chartDataDomain={domain.elements}
              columnCounts={columnCountsByXAxisValues}
              maxColumn={maxColumn}
              onClick={handleGetClickedElementData}
            />
          ) : (
            <LoadingIndicator />
          )}
          {clickedElement && (
            <>
              <Divider flexItem className="informations-divider">
                <Chip
                  label={<FormattedMessage id="waffleVisualization.selectedText" />}
                  size="small"
                  deleteIcon={<CloseIcon />}
                  onDelete={handleClose}
                />
              </Divider>
              <ResultPair result={clickedElement} />
            </>
          )}
        </div>
      </Card>
    </div>
  );
};

export default WaffleVisualization;
