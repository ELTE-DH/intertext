import { useHistory } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { FormattedMessage } from 'react-intl';
import { Avatar, Button, Card, CardContent, CardHeader } from '@mui/material';
import { BarChart as ChartIcon, MenuBook as BookIcon } from '@mui/icons-material';
import classNames from 'classnames';

import { setClickedElement } from '../../store/actions/visualizationAction';

const ResultCard = ({ type, result }) => {
  const history = useHistory();
  const dispatch = useDispatch();
  const { file_id } = useSelector(reduxState => reduxState.visualization);
  const { metadata } = useSelector(reduxState => reduxState.search);

  const handleGoToReadPage = fileId => {
    history.push(`/read/${fileId}`);
  };

  const handleGoToVisualizationPage = () => {
    const id = result[`${type}_file_id`];

    if (id.toString() === file_id) {
      dispatch(setClickedElement({ clickedElement: null }));
      return;
    }

    history.push({ pathname: `/waffle-chart/${id}`, search: `?type=${type}` });
  };

  const actionButtons = [
    { translationKey: 'read', icon: <BookIcon fontSize="small" />, onClick: handleGoToReadPage },
    {
      translationKey: 'visualize',
      icon: <ChartIcon fontSize="small" />,
      onClick: handleGoToVisualizationPage,
    },
  ];

  const getAuthorThumbnailSrc = workId => {
    let src = metadata.find(data => data.id === workId).image;

    if (src === 'default') {
      src = '';
    }

    return src;
  };

  return (
    <Card className={classNames('result-card', type)}>
      <CardHeader
        avatar={<Avatar src={getAuthorThumbnailSrc(result[`${type}_file_id`])} />}
        title={<span title={result[`${type}_title`]}>{result[`${type}_title`]}</span>}
        subheader={`${result[`${type}_author`]}${
          result[`${type}_year`] && `, ${result[`${type}_year`]}`
        }`}
      />
      <CardContent>
        <div className="buttons">
          {actionButtons.map(({ translationKey, icon, onClick }) => (
            <Button
              key={translationKey}
              size="small"
              onClick={() => onClick(result[`${type}_file_id`])}
            >
              {icon}
              <span>
                <FormattedMessage id={`buttons.${translationKey}`} />
              </span>
            </Button>
          ))}
        </div>
        <div className="text">
          <span
            dangerouslySetInnerHTML={{ __html: result[`${type}_prematch`] }}
            className="prematch"
          />{' '}
          <span dangerouslySetInnerHTML={{ __html: result[`${type}_match`] }} className="match" />{' '}
          <span
            dangerouslySetInnerHTML={{ __html: result[`${type}_postmatch`] }}
            className="postmatch"
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default ResultCard;
