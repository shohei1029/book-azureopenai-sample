import { useRef, useState } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, IDropdownOption, Dropdown } from "@fluentui/react";

import styles from "./OneShot.module.css";

import { askApi, Approaches, AskResponse, AskRequest, RetrievalMode } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList } from "../../components/Example";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";

export function Component(): JSX.Element {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [approach, setApproach] = useState<Approaches>(Approaches.RetrieveThenRead);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(RetrievalMode.Text);
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(false);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");

    const lastQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<AskResponse>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const request: AskRequest = {
                question,
                approach,
                overrides: {
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    promptTemplatePrefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                    promptTemplateSuffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                    excludeCategory: excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: retrieveCount,
                    retrievalMode: retrievalMode,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions
                }
            };
            const result = await askApi(request);
            setAnswer(result);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onPromptTemplatePrefixChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplatePrefix(newValue || "");
    };

    const onPromptTemplateSuffixChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplateSuffix(newValue || "");
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onRetrievalModeChange = (_ev: React.FormEvent<HTMLDivElement>, option?: IDropdownOption<RetrievalMode> | undefined, index?: number | undefined) => {
        setRetrievalMode(option?.data || RetrievalMode.Hybrid);
    };

    const onApproachChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        setApproach((option?.key as Approaches) || Approaches.RetrieveThenRead);
    };

    const onUseSemanticRankerChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticRanker(!!checked);
    };

    const onUseSemanticCaptionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticCaptions(!!checked);
    };

    const onExcludeCategoryChanged = (_ev?: React.FormEvent, newValue?: string) => {
        setExcludeCategory(newValue || "");
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onShowCitation = (citation: string) => {
        if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveCitation(citation);
            setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
        }
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }
    };

    const approaches: IChoiceGroupOption[] = [
        {
            key: Approaches.RetrieveThenRead,
            text: "一問一答"
        },
        {
            key: Approaches.ReadRetrieveRead,
            text: "ツール選定（ReAct）"
        },
        {
            key: Approaches.ReadPluginsRetrieve,
            text: "ChatGPT プラグイン"
        }
    ];

    return (
        <div className={styles.oneshotContainer}>
            <div className={styles.oneshotTopSection}>
                <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                <h1 className={styles.oneshotTitle}>Ask your data</h1>
                <div className={styles.oneshotQuestionInput}>
                    <QuestionInput placeholder="こちらに質問をどうぞ" disabled={isLoading} onSend={question => makeApiRequest(question)} />
                </div>
            </div>
            <div className={styles.oneshotBottomSection}>
                {isLoading && <Spinner label="回答を生成しています..." />}
                {!lastQuestionRef.current && <ExampleList onExampleClicked={onExampleClicked} />}
                {!isLoading && answer && !error && (
                    <div className={styles.oneshotAnswerContainer}>
                        <Answer
                            answer={answer}
                            isStreaming={false}
                            onCitationClicked={x => onShowCitation(x)}
                            onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                            onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                        />
                    </div>
                )}
                {error ? (
                    <div className={styles.oneshotAnswerContainer}>
                        <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                    </div>
                ) : null}
                {activeAnalysisPanelTab && answer && (
                    <AnalysisPanel
                        className={styles.oneshotAnalysisPanel}
                        activeCitation={activeCitation}
                        onActiveTabChanged={x => onToggleTab(x)}
                        citationHeight="600px"
                        answer={answer}
                        activeTab={activeAnalysisPanelTab}
                    />
                )}
            </div>

            <Panel
                headerText="回答生成の設定"
                isOpen={isConfigPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsConfigPanelOpen(false)}
                closeButtonAriaLabel="Close"
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                isFooterAtBottom={true}
            >
                <ChoiceGroup
                    className={styles.oneshotSettingsSeparator}
                    label="アプローチ"
                    options={approaches}
                    defaultSelectedKey={approach}
                    onChange={onApproachChange}
                />

                {(approach === Approaches.RetrieveThenRead || approach === Approaches.ReadDecomposeAsk) && (
                    <TextField
                        className={styles.oneshotSettingsSeparator}
                        defaultValue={promptTemplate}
                        label="プロンプトテンプレートを上書きする"
                        multiline
                        autoAdjustHeight
                        onChange={onPromptTemplateChange}
                    />
                )}

                {approach === Approaches.ReadRetrieveRead && (
                    <>
                        <TextField
                            className={styles.oneshotSettingsSeparator}
                            defaultValue={promptTemplatePrefix}
                            label="プロンプト接頭辞テンプレートを上書き"
                            multiline
                            autoAdjustHeight
                            onChange={onPromptTemplatePrefixChange}
                        />
                        <TextField
                            className={styles.oneshotSettingsSeparator}
                            defaultValue={promptTemplateSuffix}
                            label="プロンプト接尾辞テンプレートを上書き"
                            multiline
                            autoAdjustHeight
                            onChange={onPromptTemplateSuffixChange}
                        />
                    </>
                )}

                <SpinButton
                    className={styles.oneshotSettingsSeparator}
                    label="検索からこの数の文書を取得:"
                    min={1}
                    max={50}
                    defaultValue={retrieveCount.toString()}
                    onChange={onRetrieveCountChange}
                />
                <TextField className={styles.oneshotSettingsSeparator} label="除外カテゴリー" onChange={onExcludeCategoryChanged} />
                <Checkbox
                    className={styles.oneshotSettingsSeparator}
                    checked={useSemanticRanker}
                    label="検索にセマンティックランカーを使う"
                    onChange={onUseSemanticRankerChange}
                />
                <Checkbox
                    className={styles.oneshotSettingsSeparator}
                    checked={useSemanticCaptions}
                    label="文書全体ではなく、クエリコンテキストサマリーを使用する"
                    onChange={onUseSemanticCaptionsChange}
                    disabled={!useSemanticRanker}
                />
                <Dropdown
                    className={styles.oneshotSettingsSeparator}
                    label="検索モード"
                    options={[
                        { key: "hybrid", text: "Vectors + Text (Hybrid)", selected: retrievalMode == RetrievalMode.Hybrid, data: RetrievalMode.Hybrid },
                        { key: "vectors", text: "Vectors", selected: retrievalMode == RetrievalMode.Vectors, data: RetrievalMode.Vectors },
                        { key: "text", text: "Text", selected: retrievalMode == RetrievalMode.Text, data: RetrievalMode.Text }
                    ]}
                    required
                    onChange={onRetrievalModeChange}
                />
            </Panel>
        </div>
    );
}

Component.displayName = "OneShot";
