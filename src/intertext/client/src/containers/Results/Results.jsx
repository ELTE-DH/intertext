import { useEffect, useMemo, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { getSearchResults } from '../../store/actions/searchAction';

import NoResults from '../NoResults/NoResults';
import ResultPair from '../../components/ResultPair/ResultPair';

const useOnScreen = (elementRef, displayedResults) => {
  const [isIntersecting, setIntersecting] = useState(false);

  const observer = useMemo(
    () => new IntersectionObserver(([entry]) => setIntersecting(entry.isIntersecting)),
    [elementRef]
  );

  useEffect(() => {
    if (elementRef.current) observer.observe(elementRef.current);
    return () => observer.disconnect();
  }, [displayedResults]);

  return isIntersecting;
};

const Results = () => {
  const {
    data: { matchIds },
    results: { displayedResults },
    pagination: { currentPage, totalPage },
  } = useSelector(reduxState => reduxState.search);
  const lastResultPair = useRef();
  const dispatch = useDispatch();
  const isLastElementVisible = useOnScreen(lastResultPair, displayedResults);

  useEffect(() => {
    const newPage = currentPage + 1;

    if (newPage > totalPage || !matchIds.length || !isLastElementVisible) {
      return;
    }

    dispatch(getSearchResults(matchIds, newPage));
  }, [matchIds, isLastElementVisible]);

  return displayedResults.length ? (
    <div className="results">
      {displayedResults.map((result, index) => (
        <ResultPair
          key={index}
          reference={displayedResults.length === index + 1 ? lastResultPair : null}
          result={result}
        />
      ))}
    </div>
  ) : (
    <NoResults />
  );
};

export default Results;
