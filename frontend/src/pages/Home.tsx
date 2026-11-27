
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Video,
  ClipboardList,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Clock,
  Download
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { api } from '../services/api';
import { ScreeningSession, Patient } from '../types';
import { formatDateTime } from '../lib/utils';

interface HomeProps {
  onStartAssessment: () => void;
  onOpenLiveVideo: () => void;
  onViewResults: (sessionId?: string) => void;
  onViewReports: () => void;
  onViewAbout: () => void;
  onOpenResearchML?: () => void;
}

const translations = {
  en: {
    academic: 'Academic Screening-Support Prototype',
    heading: 'Objective Early Autism Screening Support',
    description: 'NeuroScreen AI combines caregiver developmental observations with behavioral video analysis to provide transparent screening support for parents, teachers and healthcare professionals.',
    start: 'Start New Assessment',
    live: 'Live Video Assessment',
    research: 'Research ML Engine',
    learn: 'Learn More',
    questionnaire: '1. Developmental Questionnaire',
    questionnaireDesc: 'Structured questions for parents and educators about early communication, social interaction, response to name and play routines.',
    milestones: 'Standardized Milestones',
    videoTitle: '2. Live Video Assessment',
    videoDesc: 'Camera-based observation of joint attention, natural gaze shifts and movement during play. No facial diagnosis or emotion guessing.',
    behaviors: 'Observable Behaviors',
    report: '3. Screening-Support Report',
    reportDesc: 'An easy-to-read summary of behavioral observations, pediatric follow-up recommendations and downloadable PDF reports.',
    pdf: 'Instant PDF Download',
    how: 'How NeuroScreen AI Works',
    howDesc: 'A simple six-step assessment process designed for clarity and demonstration.',
    steps: [
      ['Enter Child Details', 'Provide an anonymous participant ID, age in months and guardian consent.'],
      ['Complete Questionnaire', 'Answer eight caregiver questions about speech, eye contact and social play.'],
      ['Live Video Observation', 'Record a brief 15–30 second camera interaction, or skip if unavailable.'],
      ['Review Observations', 'Review questionnaire responses and computer vision behavioral metrics.'],
      ['Generate Summary', 'Use the screening model to provide objective screening-support guidance.'],
      ['Download Report', 'View the summary and save the de-identified PDF report.']
    ],
    step: 'Step',
    begin: 'Begin Assessment Workflow',
    recent: 'Recent Assessments',
    recentDesc: 'Quickly access or download completed screening reports.',
    allReports: 'View All Reports',
    view: 'View',
    typical: 'Typical Observations',
    monitoring: 'Developmental Monitoring',
    clinical: 'Clinical Evaluation Recommended',
    participant: 'Participant',
    ageNA: 'Age N/A',
    months: 'months',
    download: 'Download PDF',
    downloadError: 'Download error',
    notice: 'Academic Screening-Support Prototype – Non-Diagnostic Notice',
    noticeDesc: 'NeuroScreen AI is designed for academic research, developmental monitoring and screening support. It provides behavioral metrics to support healthcare professionals, educators and parents. It is not a medical diagnosis. Autism Spectrum Disorder diagnosis requires a comprehensive clinical evaluation by a qualified specialist using established clinical standards such as ADOS-2 or ADI-R.'
  },
  kn: {
    academic: 'ಶೈಕ್ಷಣಿಕ ತಪಾಸಣೆ-ಸಹಾಯ ಮಾದರಿ',
    heading: 'ಆಟಿಸಂನ ಆರಂಭಿಕ ತಪಾಸಣೆಗೆ ವಸ್ತುನಿಷ್ಠ ಸಹಾಯ',
    description: 'NeuroScreen AI ಪೋಷಕರು, ಶಿಕ್ಷಕರು ಮತ್ತು ಆರೋಗ್ಯ ವೃತ್ತಿಪರರಿಗೆ ತಪಾಸಣೆ ಸಹಾಯ ಒದಗಿಸಲು ಬೆಳವಣಿಗೆಯ ಗಮನಿಕೆಗಳನ್ನು ಮತ್ತು ವೀಡಿಯೊ ವಿಶ್ಲೇಷಣೆಯನ್ನು ಸಂಯೋಜಿಸುತ್ತದೆ.',
    start: 'ಹೊಸ ಮೌಲ್ಯಮಾಪನ ಪ್ರಾರಂಭಿಸಿ',
    live: 'ನೇರ ವೀಡಿಯೊ ಮೌಲ್ಯಮಾಪನ',
    research: 'ಸಂಶೋಧನಾ ML ಎಂಜಿನ್',
    learn: 'ಇನ್ನಷ್ಟು ತಿಳಿಯಿರಿ',
    questionnaire: '1. ಬೆಳವಣಿಗೆಯ ಪ್ರಶ್ನಾವಳಿ',
    questionnaireDesc: 'ಆರಂಭಿಕ ಸಂವಹನ, ಸಾಮಾಜಿಕ ಸಂಪರ್ಕ, ಹೆಸರಿಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಮತ್ತು ಆಟದ ಅಭ್ಯಾಸಗಳ ಕುರಿತು ಪೋಷಕರು ಮತ್ತು ಶಿಕ್ಷಕರಿಗಾಗಿ ಪ್ರಶ್ನೆಗಳು.',
    milestones: 'ಪ್ರಮಾಣಿತ ಬೆಳವಣಿಗೆಯ ಹಂತಗಳು',
    videoTitle: '2. ನೇರ ವೀಡಿಯೊ ಮೌಲ್ಯಮಾಪನ',
    videoDesc: 'ಆಟದ ಸಮಯದಲ್ಲಿ ಜಂಟಿ ಗಮನ, ಸಹಜ ದೃಷ್ಟಿ ಬದಲಾವಣೆ ಮತ್ತು ಚಲನೆಯ ಕ್ಯಾಮೆರಾ ಆಧಾರಿತ ವೀಕ್ಷಣೆ.',
    behaviors: 'ಗಮನಿಸಬಹುದಾದ ವರ್ತನೆಗಳು',
    report: '3. ತಪಾಸಣೆ ಸಹಾಯ ವರದಿ',
    reportDesc: 'ವರ್ತನೆಯ ಗಮನಿಕೆಗಳು, ಮಕ್ಕಳ ವೈದ್ಯರ ಮುಂದಿನ ಸಲಹೆಗಳು ಮತ್ತು ಡೌನ್‌ಲೋಡ್ ಮಾಡಬಹುದಾದ PDF ವರದಿಗಳ ಸರಳ ಸಾರಾಂಶ.',
    pdf: 'ತಕ್ಷಣ PDF ಡೌನ್‌ಲೋಡ್',
    how: 'NeuroScreen AI ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ',
    howDesc: 'ಸ್ಪಷ್ಟತೆಗಾಗಿ ರೂಪಿಸಲಾದ ಆರು ಹಂತಗಳ ಮೌಲ್ಯಮಾಪನ ಪ್ರಕ್ರಿಯೆ.',
    steps: [
      ['ಮಗುವಿನ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ', 'ಅನಾಮಧೇಯ ಭಾಗವಹಿಸುವವರ ID, ತಿಂಗಳಲ್ಲಿನ ವಯಸ್ಸು ಮತ್ತು ಪೋಷಕರ ಒಪ್ಪಿಗೆಯನ್ನು ನೀಡಿ.'],
      ['ಪ್ರಶ್ನಾವಳಿಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ', 'ಮಾತು, ಕಣ್ಣಿನ ಸಂಪರ್ಕ ಮತ್ತು ಸಾಮಾಜಿಕ ಆಟದ ಕುರಿತು ಎಂಟು ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಿ.'],
      ['ನೇರ ವೀಡಿಯೊ ವೀಕ್ಷಣೆ', '15–30 ಸೆಕೆಂಡುಗಳ ಕ್ಯಾಮೆರಾ ಸಂವಹನವನ್ನು ದಾಖಲಿಸಿ ಅಥವಾ ಲಭ್ಯವಿಲ್ಲದಿದ್ದರೆ ಬಿಟ್ಟುಬಿಡಿ.'],
      ['ಗಮನಿಕೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ', 'ಪ್ರಶ್ನಾವಳಿ ಉತ್ತರಗಳು ಮತ್ತು ಕಂಪ್ಯೂಟರ್ ದೃಷ್ಟಿ ವರ್ತನೆಯ ಅಳತೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.'],
      ['ಸಾರಾಂಶ ರಚಿಸಿ', 'ತಪಾಸಣೆ ಸಹಾಯ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಮಾದರಿಯನ್ನು ಬಳಸಿ.'],
      ['ವರದಿಯನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ', 'ಸಾರಾಂಶವನ್ನು ವೀಕ್ಷಿಸಿ ಮತ್ತು ಗುರುತು ತೆಗೆದ PDF ವರದಿಯನ್ನು ಉಳಿಸಿ.']
    ],
    step: 'ಹಂತ',
    begin: 'ಮೌಲ್ಯಮಾಪನ ಪ್ರಾರಂಭಿಸಿ',
    recent: 'ಇತ್ತೀಚಿನ ಮೌಲ್ಯಮಾಪನಗಳು',
    recentDesc: 'ಪೂರ್ಣಗೊಂಡ ತಪಾಸಣೆ ವರದಿಗಳನ್ನು ವೀಕ್ಷಿಸಿ ಅಥವಾ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.',
    allReports: 'ಎಲ್ಲಾ ವರದಿಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
    view: 'ವೀಕ್ಷಿಸಿ',
    typical: 'ಸಾಮಾನ್ಯ ಗಮನಿಕೆಗಳು',
    monitoring: 'ಬೆಳವಣಿಗೆಯ ಮೇಲ್ವಿಚಾರಣೆ',
    clinical: 'ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ',
    participant: 'ಭಾಗವಹಿಸುವವರು',
    ageNA: 'ವಯಸ್ಸು ಲಭ್ಯವಿಲ್ಲ',
    months: 'ತಿಂಗಳುಗಳು',
    download: 'PDF ಡೌನ್‌ಲೋಡ್',
    downloadError: 'ಡೌನ್‌ಲೋಡ್ ದೋಷ',
    notice: 'ಶೈಕ್ಷಣಿಕ ತಪಾಸಣೆ ಸಹಾಯ ಮಾದರಿ – ವೈದ್ಯಕೀಯ ರೋಗನಿರ್ಣಯವಲ್ಲ',
    noticeDesc: 'NeuroScreen AI ಶೈಕ್ಷಣಿಕ ಸಂಶೋಧನೆ, ಬೆಳವಣಿಗೆಯ ಮೇಲ್ವಿಚಾರಣೆ ಮತ್ತು ತಪಾಸಣೆ ಸಹಾಯಕ್ಕಾಗಿ ವಿನ್ಯಾಸಗೊಳಿಸಲಾಗಿದೆ. ಇದು ವೈದ್ಯಕೀಯ ರೋಗನಿರ್ಣಯವಲ್ಲ. ಆಟಿಸಂ ಸ್ಪೆಕ್ಟ್ರಮ್ ಡಿಸಾರ್ಡರ್ ಪತ್ತೆಗೆ ಅರ್ಹ ತಜ್ಞರಿಂದ ಸಮಗ್ರ ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ ಅಗತ್ಯವಿದೆ.'
  },
  hi: {
    academic: 'शैक्षणिक स्क्रीनिंग-सहायता प्रोटोटाइप',
    heading: 'ऑटिज़्म की शुरुआती स्क्रीनिंग में वस्तुनिष्ठ सहायता',
    description: 'NeuroScreen AI माता-पिता, शिक्षकों और स्वास्थ्य पेशेवरों के लिए विकास संबंधी अवलोकनों और वीडियो विश्लेषण के माध्यम से स्क्रीनिंग सहायता प्रदान करता है।',
    start: 'नया मूल्यांकन शुरू करें',
    live: 'लाइव वीडियो मूल्यांकन',
    research: 'रिसर्च ML इंजन',
    learn: 'और जानें',
    questionnaire: '1. विकास संबंधी प्रश्नावली',
    questionnaireDesc: 'शुरुआती संचार, सामाजिक संपर्क, नाम पर प्रतिक्रिया और खेल की आदतों के बारे में माता-पिता और शिक्षकों के लिए प्रश्न।',
    milestones: 'मानकीकृत विकासात्मक पड़ाव',
    videoTitle: '2. लाइव वीडियो मूल्यांकन',
    videoDesc: 'खेल के दौरान संयुक्त ध्यान, स्वाभाविक दृष्टि और गतिविधियों का कैमरे से अवलोकन।',
    behaviors: 'देखे जा सकने वाले व्यवहार',
    report: '3. स्क्रीनिंग-सहायता रिपोर्ट',
    reportDesc: 'व्यवहार संबंधी अवलोकनों, बाल रोग विशेषज्ञ से आगे की सलाह और डाउनलोड करने योग्य PDF रिपोर्ट का सरल सारांश।',
    pdf: 'तुरंत PDF डाउनलोड',
    how: 'NeuroScreen AI कैसे काम करता है',
    howDesc: 'स्पष्टता के लिए बनाई गई छह चरणों वाली मूल्यांकन प्रक्रिया।',
    steps: [
      ['बच्चे का विवरण दर्ज करें', 'गुमनाम प्रतिभागी ID, महीनों में उम्र और अभिभावक की सहमति दें।'],
      ['प्रश्नावली पूरी करें', 'बोलने, आँखों के संपर्क और सामाजिक खेल के बारे में आठ प्रश्नों के उत्तर दें।'],
      ['लाइव वीडियो अवलोकन', '15–30 सेकंड का कैमरा वीडियो रिकॉर्ड करें या उपलब्ध न होने पर छोड़ दें।'],
      ['अवलोकनों की समीक्षा करें', 'प्रश्नावली के उत्तर और कंप्यूटर विज़न व्यवहार संबंधी माप देखें।'],
      ['सारांश तैयार करें', 'स्क्रीनिंग सहायता मार्गदर्शन के लिए मॉडल का उपयोग करें।'],
      ['रिपोर्ट डाउनलोड करें', 'सारांश देखें और पहचान हटाई गई PDF रिपोर्ट सहेजें।']
    ],
    step: 'चरण',
    begin: 'मूल्यांकन प्रक्रिया शुरू करें',
    recent: 'हाल के मूल्यांकन',
    recentDesc: 'पूरी हुई स्क्रीनिंग रिपोर्ट देखें या डाउनलोड करें।',
    allReports: 'सभी रिपोर्ट देखें',
    view: 'देखें',
    typical: 'सामान्य अवलोकन',
    monitoring: 'विकास संबंधी निगरानी',
    clinical: 'क्लिनिकल मूल्यांकन की सलाह',
    participant: 'प्रतिभागी',
    ageNA: 'उम्र उपलब्ध नहीं',
    months: 'महीने',
    download: 'PDF डाउनलोड',
    downloadError: 'डाउनलोड त्रुटि',
    notice: 'शैक्षणिक स्क्रीनिंग-सहायता प्रोटोटाइप – चिकित्सा निदान नहीं',
    noticeDesc: 'NeuroScreen AI शैक्षणिक अनुसंधान, विकास संबंधी निगरानी और स्क्रीनिंग सहायता के लिए बनाया गया है। यह चिकित्सा निदान नहीं है। ऑटिज़्म स्पेक्ट्रम डिसऑर्डर के निदान के लिए योग्य विशेषज्ञ द्वारा व्यापक नैदानिक मूल्यांकन आवश्यक है।'
  },
  te: {
    academic: 'విద్యాపరమైన స్క్రీనింగ్ సహాయ నమూనా',
    heading: 'ఆటిజం ప్రారంభ స్క్రీనింగ్‌కు వాస్తవ ఆధారిత సహాయం',
    description: 'NeuroScreen AI తల్లిదండ్రులు, ఉపాధ్యాయులు మరియు ఆరోగ్య నిపుణులకు అభివృద్ధి పరిశీలనలు మరియు వీడియో విశ్లేషణ ద్వారా స్క్రీనింగ్ సహాయం అందిస్తుంది.',
    start: 'కొత్త అంచనాను ప్రారంభించండి',
    live: 'లైవ్ వీడియో అంచనా',
    research: 'రీసెర్చ్ ML ఇంజిన్',
    learn: 'మరింత తెలుసుకోండి',
    questionnaire: '1. అభివృద్ధి ప్రశ్నావళి',
    questionnaireDesc: 'ప్రారంభ సంభాషణ, సామాజిక పరస్పర చర్య, పేరు పిలిచినప్పుడు స్పందన మరియు ఆట అలవాట్లపై ప్రశ్నలు.',
    milestones: 'ప్రామాణిక అభివృద్ధి దశలు',
    videoTitle: '2. లైవ్ వీడియో అంచనా',
    videoDesc: 'ఆట సమయంలో ఉమ్మడి శ్రద్ధ, సహజ చూపు మార్పులు మరియు కదలికలను కెమెరా ద్వారా పరిశీలించడం.',
    behaviors: 'గమనించగల ప్రవర్తనలు',
    report: '3. స్క్రీనింగ్ సహాయ నివేదిక',
    reportDesc: 'ప్రవర్తనా పరిశీలనలు, పిల్లల వైద్యుడిని సంప్రదించడానికి సూచనలు మరియు డౌన్‌లోడ్ చేయగల PDF నివేదికల సారాంశం.',
    pdf: 'తక్షణ PDF డౌన్‌లోడ్',
    how: 'NeuroScreen AI ఎలా పనిచేస్తుంది',
    howDesc: 'స్పష్టత కోసం రూపొందించిన ఆరు దశల అంచనా ప్రక్రియ.',
    steps: [
      ['పిల్లల వివరాలను నమోదు చేయండి', 'అనామక పాల్గొనేవారి ID, నెలల్లో వయస్సు మరియు సంరక్షకుల సమ్మతిని ఇవ్వండి.'],
      ['ప్రశ్నావళిని పూర్తి చేయండి', 'మాట్లాడటం, కంటి చూపు మరియు సామాజిక ఆట గురించి ఎనిమిది ప్రశ్నలకు సమాధానం ఇవ్వండి.'],
      ['లైవ్ వీడియో పరిశీలన', '15–30 సెకన్ల కెమెరా పరస్పర చర్యను రికార్డ్ చేయండి లేదా అందుబాటులో లేకపోతే దాటవేయండి.'],
      ['పరిశీలనలను సమీక్షించండి', 'ప్రశ్నావళి సమాధానాలు మరియు కంప్యూటర్ విజన్ ప్రవర్తనా కొలమానాలను చూడండి.'],
      ['సారాంశాన్ని రూపొందించండి', 'స్క్రీనింగ్ సహాయ మార్గదర్శకత్వం కోసం మోడల్‌ను ఉపయోగించండి.'],
      ['నివేదికను డౌన్‌లోడ్ చేయండి', 'సారాంశాన్ని చూసి గుర్తింపు తొలగించిన PDF నివేదికను సేవ్ చేయండి.']
    ],
    step: 'దశ',
    begin: 'అంచనా ప్రక్రియను ప్రారంభించండి',
    recent: 'ఇటీవలి అంచనాలు',
    recentDesc: 'పూర్తయిన స్క్రీనింగ్ నివేదికలను చూడండి లేదా డౌన్‌లోడ్ చేయండి.',
    allReports: 'అన్ని నివేదికలను చూడండి',
    view: 'చూడండి',
    typical: 'సాధారణ పరిశీలనలు',
    monitoring: 'అభివృద్ధి పర్యవేక్షణ',
    clinical: 'వైద్య మూల్యాంకనం సిఫార్సు చేయబడింది',
    participant: 'పాల్గొనేవారు',
    ageNA: 'వయస్సు అందుబాటులో లేదు',
    months: 'నెలలు',
    download: 'PDF డౌన్‌లోడ్',
    downloadError: 'డౌన్‌లోడ్ లోపం',
    notice: 'విద్యాపరమైన స్క్రీనింగ్ సహాయ నమూనా – వైద్య నిర్ధారణ కాదు',
    noticeDesc: 'NeuroScreen AI విద్యాపరమైన పరిశోధన, అభివృద్ధి పర్యవేక్షణ మరియు స్క్రీనింగ్ సహాయం కోసం రూపొందించబడింది. ఇది వైద్య నిర్ధారణ కాదు. ఆటిజం స్పెక్ట్రమ్ డిజార్డర్ నిర్ధారణకు అర్హత కలిగిన నిపుణుడి సమగ్ర వైద్య మూల్యాంకనం అవసరం.'
  },
  ta: {
    academic: 'கல்விசார் பரிசோதனை ஆதரவு முன்மாதிரி',
    heading: 'ஆட்டிசத்தின் ஆரம்பகால பரிசோதனைக்கு ஆதரவு',
    description: 'NeuroScreen AI பெற்றோர், ஆசிரியர்கள் மற்றும் சுகாதார நிபுணர்களுக்கு வளர்ச்சி கவனிப்புகள் மற்றும் காணொளி பகுப்பாய்வு மூலம் பரிசோதனை ஆதரவை வழங்குகிறது.',
    start: 'புதிய மதிப்பீட்டைத் தொடங்கு',
    live: 'நேரடி காணொளி மதிப்பீடு',
    research: 'ஆராய்ச்சி ML இயந்திரம்',
    learn: 'மேலும் அறிக',
    questionnaire: '1. வளர்ச்சி கேள்வித்தாள்',
    questionnaireDesc: 'ஆரம்பகால தொடர்பு, சமூக உறவு, பெயருக்கு பதிலளித்தல் மற்றும் விளையாட்டு பழக்கங்கள் பற்றிய கேள்விகள்.',
    milestones: 'தரப்படுத்தப்பட்ட வளர்ச்சி நிலைகள்',
    videoTitle: '2. நேரடி காணொளி மதிப்பீடு',
    videoDesc: 'விளையாட்டின்போது கூட்டு கவனம், இயல்பான பார்வை மாற்றங்கள் மற்றும் அசைவுகளை கேமரா மூலம் கவனித்தல்.',
    behaviors: 'கவனிக்கக்கூடிய நடத்தைகள்',
    report: '3. பரிசோதனை ஆதரவு அறிக்கை',
    reportDesc: 'நடத்தை கவனிப்புகள், குழந்தை மருத்துவரை அணுகுவதற்கான பரிந்துரைகள் மற்றும் பதிவிறக்கக்கூடிய PDF அறிக்கைகளின் சுருக்கம்.',
    pdf: 'உடனடி PDF பதிவிறக்கம்',
    how: 'NeuroScreen AI எவ்வாறு செயல்படுகிறது',
    howDesc: 'தெளிவுக்காக வடிவமைக்கப்பட்ட ஆறு படிநிலை மதிப்பீட்டு செயல்முறை.',
    steps: [
      ['குழந்தையின் விவரங்களை உள்ளிடவும்', 'அடையாளமற்ற பங்கேற்பாளர் ID, மாதங்களில் வயது மற்றும் பாதுகாவலர் ஒப்புதலை வழங்கவும்.'],
      ['கேள்வித்தாளை முடிக்கவும்', 'பேச்சு, கண் தொடர்பு மற்றும் சமூக விளையாட்டு பற்றிய எட்டு கேள்விகளுக்கு பதிலளிக்கவும்.'],
      ['நேரடி காணொளி கவனிப்பு', '15–30 விநாடி கேமரா தொடர்பைப் பதிவு செய்யவும் அல்லது வசதி இல்லையெனில் தவிர்க்கவும்.'],
      ['கவனிப்புகளை மதிப்பாய்வு செய்யவும்', 'கேள்வித்தாள் பதில்கள் மற்றும் கணினி பார்வை நடத்தை அளவீடுகளைப் பார்க்கவும்.'],
      ['சுருக்கத்தை உருவாக்கவும்', 'பரிசோதனை ஆதரவு வழிகாட்டுதலுக்கு மாதிரியைப் பயன்படுத்தவும்.'],
      ['அறிக்கையைப் பதிவிறக்கவும்', 'சுருக்கத்தைப் பார்த்து அடையாளம் நீக்கப்பட்ட PDF அறிக்கையைச் சேமிக்கவும்.']
    ],
    step: 'படி',
    begin: 'மதிப்பீட்டு செயல்முறையைத் தொடங்கு',
    recent: 'சமீபத்திய மதிப்பீடுகள்',
    recentDesc: 'முடிக்கப்பட்ட பரிசோதனை அறிக்கைகளைப் பார்க்கவும் அல்லது பதிவிறக்கவும்.',
    allReports: 'அனைத்து அறிக்கைகளையும் காண்க',
    view: 'காண்க',
    typical: 'வழக்கமான கவனிப்புகள்',
    monitoring: 'வளர்ச்சி கண்காணிப்பு',
    clinical: 'மருத்துவ மதிப்பீடு பரிந்துரைக்கப்படுகிறது',
    participant: 'பங்கேற்பாளர்',
    ageNA: 'வயது கிடைக்கவில்லை',
    months: 'மாதங்கள்',
    download: 'PDF பதிவிறக்கம்',
    downloadError: 'பதிவிறக்கப் பிழை',
    notice: 'கல்விசார் பரிசோதனை ஆதரவு முன்மாதிரி – மருத்துவ நோயறிதல் அல்ல',
    noticeDesc: 'NeuroScreen AI கல்வி ஆராய்ச்சி, வளர்ச்சி கண்காணிப்பு மற்றும் பரிசோதனை ஆதரவுக்காக வடிவமைக்கப்பட்டுள்ளது. இது மருத்துவ நோயறிதல் அல்ல. ஆட்டிசம் ஸ்பெக்ட்ரம் குறைபாட்டைக் கண்டறிய தகுதியான நிபுணரின் முழுமையான மருத்துவ மதிப்பீடு அவசியம்.'
  }
};

export const Home: React.FC<HomeProps> = ({
  onStartAssessment,
  onOpenLiveVideo,
  onViewResults,
  onViewReports,
  onViewAbout,
  onOpenResearchML
}) => {
  const { i18n } = useTranslation();
  const language = (i18n.resolvedLanguage || i18n.language || 'en').split('-')[0] as keyof typeof translations;
  const c = translations[language] || translations.en;

  const [patients, setPatients] = useState<Patient[]>([]);
  const [recentScreenings, setRecentScreenings] = useState<ScreeningSession[]>([]);

  useEffect(() => {
    async function loadOverview() {
      try {
        const [screenList, patList] = await Promise.all([
          api.listScreenings(),
          api.listPatients()
        ]);
        setRecentScreenings(screenList.slice(0, 4));
        setPatients(patList);
      } catch (err) {
        console.error('Failed to load home overview data:', err);
      }
    }
    loadOverview();
  }, []);

  const getPatientAnonId = (patientId: string): string => {
    const p = patients.find((pat) => pat.id === patientId);
    return p ? p.anonymized_id : c.participant;
  };

  const getPatientAge = (patientId: string): string => {
    const p = patients.find((pat) => pat.id === patientId);
    return p ? `${p.age_months} ${c.months}` : c.ageNA;
  };

  const getRiskBadge = (tier: string) => {
    if (tier === 'LOW_LIKELIHOOD') return <Badge variant="success">{c.typical}</Badge>;
    if (tier === 'MODERATE_MONITOR') return <Badge variant="warning">{c.monitoring}</Badge>;
    if (tier === 'ELEVATED_TRIAGE_RECOMMENDED') return <Badge variant="danger">{c.clinical}</Badge>;
    return <Badge variant="default">{tier.replace(/_/g, ' ')}</Badge>;
  };

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-teal-900 via-slate-900 to-sky-950 p-8 sm:p-12 text-white shadow-xl border border-teal-800/40">
        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 bg-teal-500/20 text-teal-300 border border-teal-500/40 px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <span>{c.academic}</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">{c.heading}</h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal">{c.description}</p>
          <div className="pt-2 flex flex-wrap gap-4">
            <Button variant="primary" size="lg" onClick={onStartAssessment} className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold shadow-lg shadow-teal-500/25 border-0">
              <ClipboardList className="w-5 h-5 mr-2" />{c.start}
            </Button>
            <Button variant="outline" size="lg" onClick={onOpenLiveVideo} className="bg-white/10 hover:bg-white/20 text-white border-white/25 backdrop-blur-sm">
              <Video className="w-5 h-5 mr-2 text-teal-300" />{c.live}
            </Button>
            {onOpenResearchML && (
              <Button variant="outline" size="lg" onClick={onOpenResearchML} className="bg-teal-900/60 hover:bg-teal-800 text-teal-200 border-teal-500/40 backdrop-blur-sm">
                <Sparkles className="w-5 h-5 mr-2 text-teal-300" />{c.research}
              </Button>
            )}
            <Button variant="ghost" size="lg" onClick={onViewAbout} className="text-slate-300 hover:text-white hover:bg-white/10">{c.learn}</Button>
          </div>
        </div>
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 -mb-10 w-80 h-80 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-slate-200/80 hover:shadow-md transition-shadow bg-white">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mb-3"><ClipboardList className="w-6 h-6" /></div>
            <CardTitle className="text-lg font-bold text-slate-900">{c.questionnaire}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>{c.questionnaireDesc}</p>
            <span className="inline-block text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">{c.milestones}</span>
          </CardContent>
        </Card>

        <Card className="border-slate-200/80 hover:shadow-md transition-shadow bg-white">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mb-3"><Video className="w-6 h-6" /></div>
            <CardTitle className="text-lg font-bold text-slate-900">{c.videoTitle}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>{c.videoDesc}</p>
            <span className="inline-block text-xs font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded">{c.behaviors}</span>
          </CardContent>
        </Card>

        <Card className="border-slate-200/80 hover:shadow-md transition-shadow bg-white">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3"><FileText className="w-6 h-6" /></div>
            <CardTitle className="text-lg font-bold text-slate-900">{c.report}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>{c.reportDesc}</p>
            <span className="inline-block text-xs font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">{c.pdf}</span>
          </CardContent>
        </Card>
      </section>

      <section className="bg-slate-100/70 border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div className="max-w-2xl mb-6">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">{c.how}</h2>
          <p className="text-sm text-slate-600 mt-1">{c.howDesc}</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {c.steps.map((item, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-teal-700 uppercase tracking-wider bg-teal-50 px-2 py-0.5 rounded inline-block mb-2">{c.step} {idx + 1}</span>
                <h3 className="font-semibold text-slate-900 text-sm">{item[0]}</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{item[1]}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 flex justify-end">
          <Button variant="primary" size="md" onClick={onStartAssessment} className="bg-teal-600 hover:bg-teal-700 text-white">
            {c.begin} <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>

      {recentScreenings.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">{c.recent}</h2>
              <p className="text-xs text-slate-500">{c.recentDesc}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={onViewReports} className="text-teal-700 hover:text-teal-800">
              {c.allReports} <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentScreenings.map((session) => (
              <Card key={session.id} className="border-slate-200 hover:border-teal-300 transition-colors">
                <CardContent className="p-4 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900">{getPatientAnonId(session.patient_id)}</span>
                      <span className="text-xs text-slate-500 font-medium">({getPatientAge(session.patient_id)})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {getRiskBadge(session.risk_tier)}
                      <span className="text-[11px] text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3" />{formatDateTime(session.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => onViewResults(session.id)} className="text-xs">{c.view}</Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={async () => {
                        try {
                          const blob = await api.downloadReportPdf(session.id);
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `screening_report_${session.id.slice(0, 8)}.pdf`;
                          a.click();
                          URL.revokeObjectURL(url);
                        } catch (err: any) {
                          alert(`${c.downloadError}: ${err.message}`);
                        }
                      }}
                      className="text-teal-700 hover:text-teal-800 hover:bg-teal-50 text-xs"
                      title={c.download}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      <section className="bg-amber-50/70 border border-amber-200 rounded-2xl p-5 flex items-start gap-4 text-amber-900">
        <div className="p-2 bg-amber-100 rounded-xl text-amber-800 flex-shrink-0 mt-0.5"><ShieldCheck className="w-5 h-5" /></div>
        <div className="space-y-1 text-xs sm:text-sm">
          <h4 className="font-bold text-amber-950">{c.notice}</h4>
          <p className="text-amber-800 leading-relaxed">{c.noticeDesc}</p>
        </div>
      </section>
    </div>
  );
};
