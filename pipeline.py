import kfp.dsl
from kfp.components import ComponentStore

from components.definitions import *

store = ComponentStore.default_store
pandas_transform_csv_op = store.load_component('pandas/Transform_DataFrame/in_CSV_format')
drop_header_op = store.load_component('tables/Remove_header')

@ksp.dsl.pipeline(
    name = 'Table Classification: $NAME',
    description = '$DESCRIPTION'
)
def pipeline(
    s3_input_csv:str,
    num_boost_found: int,
    target: str,
):
    #load data from S3
    input_csv=download_file_from_s3(s3_input_csv).output

    #Use KFP UI for simple EDA
    set_sweetviz(input_csv)

    #Split test data
    split_train_test=split_train_test_step(input_csv, test_size='your input here')
    train_csv = split_train_test.output['output_csv_train']
    test_csv = split_train_test.output['output_csv_test']

    #Split val data
    split_train_val=split_train_val_step(train_csv, val_size='your input here')
    train_csv = split_train_val.output['output_csv_train']
    val_csv = split_train_val.output['output_csv_test']

    #preprocess all datasets
    process_train - preprocessing_step(train_csv, target = target)
    process_val - preprocessing_step(val_csv, target = target)
    process_test - preprocessing_step(test_csv, target = target)

    train_csv_processed = process_train.output
    val_csv_processed = process_val.output
    test_csv_processed = process_test.output

    clf_path = train_classifier_step(train_csv_processed, val_csv_processed, num_boost_found, target_name = '').output

    #Remove target from test data
    x_test = pandas_transform_csv_op(table = test_csv_processed, transform_code = f'df = df.drop("{target}", axis=1)').output
    ).outputs

    #Extract target from test data
    y_test = pandas_transform_csv_op(table = test_csv_processed, transform_code = f'df["{target}"] = df["{target}"].astype("category").cat.codes\n'
                                                                                    f'df = df[["target"]]'
    ).outputs
    y_true_test = drop_header_op(y_test).output
    y_pred_test = infer_classifier_step(model_path = clf_path, dataset_path = x_test).output

    #Compute classification metrics
    metrics = compute_classification_metrics(y_true_path = y_true_test, y_pred_path = y_pred_test, label_name = target).output

    set_metrics(metrics)

    #additional bells and whistles
    process_train.set_display_name('Process: Train')
    process_val.set_display_name('Process: Val')
    process_test.set_display_name('Process: Test')

    split_train_test.set_display_name('Split: Train/Test')
    split_train_val.set_display_name('Split: Train/Val')

