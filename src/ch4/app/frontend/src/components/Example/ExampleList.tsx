import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    { text: "三浦義澄って何した人", value: "三浦義澄って何した人" },
    {
        text: "源実朝は征夷大将軍として知られているだけでなく、ある有名な趣味も持っています。それは何ですか。",
        value: "源実朝は征夷大将軍として知られているだけでなく、ある有名な趣味も持っています。それは何ですか。"
    },
    { text: "源範頼の簡単な情報と、彼のゆかりの地にあるいいカフェを教えて", value: "源範頼の簡単な情報と、彼のゆかりの地にあるいいカフェを教えて" }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
