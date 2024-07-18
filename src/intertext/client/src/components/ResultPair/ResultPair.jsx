import { Chip, Divider } from '@mui/material';
import ResultCard from '../ResultCard/ResultCard';

const ResultPair = ({ reference, result }) => {
  const { similarity } = result;

  return (
    <div ref={reference || null} className="result-pair">
      <ResultCard type="source" result={result} />
      <Divider orientation="vertical" flexItem>
        <Chip label={`${similarity}%`} size="small" />
      </Divider>
      <ResultCard type="target" result={result} />
    </div>
  );
};

export default ResultPair;
