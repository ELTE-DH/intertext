import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { Card } from '@mui/material';

import { getTextFromJSON } from '../../rest/resource/resource';

import SubheaderCard from '../../components/SubheaderCard/SubheaderCard';
import Title from '../../components/Title/Title';

const Read = () => {
  const [text, setText] = useState();
  const [currentMetadata, setCurrentMetadata] = useState();
  const { id } = useParams();
  const { metadata } = useSelector(reduxState => reduxState.search);

  useEffect(() => {
    getTextFromJSON(id).then(response => setText(response.join(' ')));
  }, [id]);

  useEffect(() => {
    if (metadata.length > 0) {
      const informations = metadata.find(work => work.id.toString() === id);
      const data = {
        author: informations.author,
        title: informations.title,
        year: informations.year,
      };

      setCurrentMetadata(data);
    }
  }, [metadata]);

  return currentMetadata && text ? (
    <div className="read-page content-page">
      <SubheaderCard>
        <Title
          author={currentMetadata.author}
          year={currentMetadata.year}
          title={currentMetadata.title}
        />
      </SubheaderCard>
      <Card className="text-container">
        <div dangerouslySetInnerHTML={{ __html: text }} />
      </Card>
    </div>
  ) : (
    <div>Failed to fetch the current text!</div>
  );
};

export default Read;
